"""Node functions for each step in the LangGraph agent pipeline."""

from __future__ import annotations

import tempfile
import os
import json
from pathlib import Path
from typing import Any

from agent.state import AgentState
from tools.chunker import chunk_source_files
from tools.file_reader import read_source_files
from tools.repo_cloner import clone_repo
from tools.language_manager import detect_language, get_language_config


def clone_repo_node(state: AgentState) -> dict[str, Any]:
    """Clone the requested GitHub repository and detect its language."""

    repo_url = state.get("repo_url")
    if not repo_url:
        raise ValueError("Agent state must include repo_url")

    target_dir = state.get("clone_target_dir") or tempfile.mkdtemp(prefix="code-review-repo-")
    repo_path = clone_repo(repo_url, target_dir)
    language = detect_language(repo_path)
    return {"repo_path": repo_path, "language": language}


def read_files_node(state: AgentState) -> dict[str, Any]:
    """Read all source files and split them into review chunks dynamically."""

    repo_path = state.get("repo_path")
    language = state.get("language", "python")
    if not repo_path:
        raise ValueError("Agent state must include repo_path")

    lang_config = get_language_config(language)
    files = read_source_files(
        repo_path,
        extensions=lang_config["extensions"],
        exclude_dirs=lang_config["exclude_dirs"]
    )
    return {"files": files, "file_chunks": chunk_source_files(files, language=language)}


def static_analysis_node(state: AgentState) -> dict[str, Any]:
    """Run Bandit and Pylint recursive static analysis scans."""

    repo_path = state.get("repo_path")
    if not repo_path:
        raise ValueError("Agent state must include repo_path")

    try:
        from tools.static_analysis import run_all_static_analysis
    except ImportError:
        return {"static_analysis_results": {"status": "not_implemented"}}

    language = state.get("language", "python")
    return {"static_analysis_results": run_all_static_analysis(repo_path, language=language)}


def _clean_json_response(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def llm_bug_detection_node(state: AgentState) -> dict[str, Any]:
    """Perform logic review and security scans on code chunks using LLM."""
    from agent.prompts import BUG_DETECTION_PROMPT

    from agent.llm import get_llm
    llm = get_llm(temperature=0.1)

    # If no LLM is configured, return the fallback placeholders
    if not llm:
        print("[*] Warning: No active LLM key detected for BugDetector. Returning placeholders.")
        findings = [
            {
                "file_path": chunk["file_path"],
                "symbol": chunk["name"],
                "status": "pending_llm_review",
            }
            for chunk in state.get("file_chunks", [])
        ]
        return {"llm_findings": findings}

    findings = []
    static_results = state.get("static_analysis_results", {})
    file_chunks = state.get("file_chunks", [])

    # Count chunks per file to determine if we can skip module preambles
    from collections import Counter
    chunk_counts = Counter(chunk["file_path"] for chunk in file_chunks)
    
    # Analyze each AST code chunk
    for chunk in file_chunks:
        file_path = chunk["file_path"]
        # Skip unit test files to conserve API rate limits and avoid logical analysis on tests
        if "test_" in Path(file_path).name or "tests/" in file_path:
            continue
            
        # Skip module preambles if the file has other functions/classes to avoid redundant reviews
        if chunk["name"] == "<module>" and chunk_counts[file_path] > 1:
            continue

        # Filter static results to only include findings for this file to save token context
        file_path_obj = Path(file_path)
        file_static_results = {
            "bandit": [
                issue for issue in static_results.get("bandit", [])
                if issue.get("filename") and (
                    file_path in issue["filename"].replace('\\', '/') or Path(issue["filename"]).name == file_path_obj.name
                )
            ],
            "pylint": [
                issue for issue in static_results.get("pylint", [])
                if issue.get("path") and (
                    file_path in issue["path"].replace('\\', '/') or Path(issue["path"]).name == file_path_obj.name
                )
            ]
        }
            
        print(f"[*] AI reviewing chunk {chunk['name']} in {chunk['file_path']}...")
        prompt = BUG_DETECTION_PROMPT.format(
            file_path=chunk["file_path"],
            symbol_name=chunk["name"],
            symbol_kind=chunk["kind"],
            code_content=chunk["content"],
            static_analysis=json.dumps(file_static_results, indent=2)
        )
        
        import time
        # Throttling delay to respect Groq API rate limits
        time.sleep(2)
        response = None
        for attempt in range(3):
            try:
                response = llm.invoke(prompt)
                break
            except Exception as e:
                err_str = str(e).lower()
                if ("429" in err_str or "resource_exhausted" in err_str or "rate" in err_str) and attempt < 2:
                    print(f"[*] LLM rate limit hit. Sleeping 15s before retrying chunk {chunk['name']} (Attempt {attempt+1}/3)...")
                    time.sleep(15)
                else:
                    print(f"[*] Warning: LLM review failed for chunk {chunk['name']}: {e}")
                    break
                    
        if response:
            cleaned_res = _clean_json_response(response.content)
            if cleaned_res:
                try:
                    chunk_findings = json.loads(cleaned_res)
                    if isinstance(chunk_findings, list):
                        for finding in chunk_findings:
                            # Append code context to findings to help the FixGenerator
                            finding["code_chunk_content"] = chunk["content"]
                            finding["status"] = "identified"
                            findings.append(finding)
                except Exception as ex:
                    print(f"[*] Warning: Failed to parse findings for chunk {chunk['name']}: {ex}")

    # Fallback to placeholders if no issues found but we want code symbols tracked
    if not findings:
        findings = [
            {
                "file_path": chunk["file_path"],
                "symbol": chunk["name"],
                "status": "no_bugs_found",
            }
            for chunk in state.get("file_chunks", [])
        ]

    return {"llm_findings": findings}


def generate_fixes_node(state: AgentState) -> dict[str, Any]:
    """Generate proposed code corrections for identified issues using LLM."""
    from tools.fix_generator import generate_all_fixes

    repo_path = state.get("repo_path")
    if not repo_path:
        raise ValueError("Agent state must include repo_path")

    from agent.llm import get_llm
    llm = get_llm(temperature=0.1)

    # If no LLM is configured, return empty fixes
    if not llm:
        print("[*] Warning: No active LLM key detected for FixGenerator. Returning empty suggested_fixes.")
        return {"suggested_fixes": []}

    findings = state.get("llm_findings", [])
    suggested_fixes = generate_all_fixes(findings, repo_path, llm)
    return {"suggested_fixes": suggested_fixes}


def run_tests_node(state: AgentState) -> dict[str, Any]:
    """Run tests in the E2B sandbox if tests are present."""

    repo_path = state.get("repo_path")
    if not repo_path:
        raise ValueError("Agent state must include repo_path")

    language = state.get("language", "python")
    root = Path(repo_path)
    
    if language.lower() == "javascript":
        test_files = (
            list(root.glob("*.test.js")) +
            list(root.glob("*.spec.js")) +
            list(root.glob("**/test/*.js")) +
            list(root.glob("**/__tests__/**/*.js")) +
            list(root.glob("*.test.ts")) +
            list(root.glob("*.spec.ts"))
        )
    else:
        test_files = (
            list(root.glob("test*.py")) +
            list(root.glob("tests/test*.py")) +
            list(root.glob("**/test_*.py"))
        )
    has_tests = len(test_files) > 0

    if not has_tests:
        print("[*] No test suite detected in repository. Autogenerating basic smoke tests to bootstrap validation...")
        files = state.get("files", {})
        files_info = []
        for rel_path, content in files.items():
            # Skip test files and private hidden files
            if "test" in rel_path or rel_path.startswith(".") or rel_path.startswith("venv"):
                continue
            try:
                import ast
                tree = ast.parse(content)
                funcs = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) if not node.name.startswith("_")]
                if funcs:
                    files_info.append(f"- File: {rel_path}\n  Functions: {', '.join(funcs)}")
            except Exception:
                pass
                
        files_info_str = "\n".join(files_info)
        
        from agent.llm import get_llm
        llm = get_llm(temperature=0.1)
                
        if llm and files_info_str:
            from agent.prompts import BOOTSTRAP_TEST_PROMPT
            prompt = BOOTSTRAP_TEST_PROMPT.format(files_info=files_info_str)
            try:
                response = llm.invoke(prompt)
                test_code = response.content.strip()
                if test_code.startswith("```python"):
                    test_code = test_code[9:]
                elif test_code.startswith("```"):
                    test_code = test_code[3:]
                if test_code.endswith("```"):
                    test_code = test_code[:-3]
                test_code = test_code.strip()
                
                # Save the smoke test file locally
                tests_dir = Path(repo_path) / "tests"
                tests_dir.mkdir(parents=True, exist_ok=True)
                smoke_test_path = tests_dir / "test_autogenerated_smoke.py"
                smoke_test_path.write_text(test_code, encoding="utf-8")
                print(f"[+] Autogenerated smoke test saved to {smoke_test_path}")
                
                has_tests = True
            except Exception as e:
                print(f"[*] Warning: Failed to autogenerate smoke test: {e}")
                
    if not has_tests:
        if language.lower() == "javascript":
            return {"test_results": {"status": "no_tests_found", "has_tests": False}}
            
    if not has_tests:
        return {"test_results": {"status": "no_tests_found", "has_tests": False}}

    try:
        from tools.test_runner import run_tests_in_sandbox
        results = run_tests_in_sandbox(repo_path, language=language)
        results["has_tests"] = True
        return {"test_results": results}
    except Exception as e:
        return {
            "test_results": {
                "status": "failed",
                "error": str(e),
                "has_tests": True
            }
        }


def generate_tests_node(state: AgentState) -> dict[str, Any]:
    """Identify uncovered functions and run the AI test generator loop."""
    from tools.test_generator import generate_all_tests

    repo_path = state.get("repo_path")
    if not repo_path:
        raise ValueError("Agent state must include repo_path")

    test_results = state.get("test_results", {})
    # If no test suite was detected, we cannot analyze coverage or add unit tests
    if not test_results.get("has_tests", False) or "coverage" not in test_results:
        print("[*] Skipped test generation: No test suite or coverage telemetry found.")
        return {"generated_tests": []}

    from agent.llm import get_llm
    llm = get_llm(temperature=0.1)

    if not llm:
        print("[*] Warning: No active LLM key detected for TestGenerator. Returning empty generated_tests.")
        return {"generated_tests": []}

    files = state.get("files", {})
    generated_tests = generate_all_tests(test_results, files, repo_path, llm)
    return {"generated_tests": generated_tests}


def validate_fixes_node(state: AgentState) -> dict[str, Any]:
    """Test applied fixes inside the sandbox environment to ensure correctness."""
    from tools.fix_generator import apply_fix
    from tools.test_runner import run_tests_in_sandbox

    repo_path = state.get("repo_path")
    if not repo_path:
        raise ValueError("Agent state must include repo_path")

    suggested_fixes = state.get("suggested_fixes", [])
    if not suggested_fixes:
        return {"validation_results": {"status": "no_fixes_to_validate"}}

    test_results = state.get("test_results", {})
    # Check if a test suite is present
    if not test_results.get("has_tests", False):
        return {"validation_results": {"status": "no_tests_found_to_validate"}}

    # 1. Apply fixes locally and keep backups
    original_contents = {}
    applied_count = 0
    
    for fix in suggested_fixes:
        file_path = fix["file_path"]
        full_path = Path(repo_path) / file_path
        
        # Backup original content
        if full_path.exists() and file_path not in original_contents:
            try:
                original_contents[file_path] = full_path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"[*] Warning: Could not backup {file_path}: {e}")
                continue

        # Apply fix on local file
        success = apply_fix(
            repo_path,
            file_path,
            fix["original_code"],
            fix["fixed_code"],
            symbol=fix.get("symbol"),
            original_chunk_content=fix.get("original_chunk_content")
        )
        if success:
            applied_count += 1

    if applied_count == 0:
        return {"validation_results": {"status": "failed_to_apply_fixes_locally"}}

    # 2. Upload and run tests inside E2B sandbox
    language = state.get("language", "python")
    print(f"[*] Validating {applied_count} applied fixes in E2B sandbox...")
    validation_res = run_tests_in_sandbox(repo_path, language=language)

    # 3. Restore original files locally to keep codebase clean
    for file_path, content in original_contents.items():
        try:
            full_path = Path(repo_path) / file_path
            full_path.write_text(content, encoding="utf-8")
        except Exception as e:
            print(f"[*] Error restoring original content for {file_path}: {e}")
            
    print("[*] Local repository code restored to original state.")

    # 4. Evaluate validation results
    passed = validation_res.get("passed", 0)
    failed = validation_res.get("failed", 0)
    errors = validation_res.get("errors", 0)
    exit_code = validation_res.get("exit_code", 1)

    status = "failed"
    if exit_code == 0 and failed == 0 and errors == 0 and passed > 0:
        status = "passed"

    return {
        "validation_results": {
            "status": status,
            "exit_code": exit_code,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "stdout": validation_res.get("stdout", ""),
            "stderr": validation_res.get("stderr", "")
        }
    }


def build_report_node(state: AgentState) -> dict[str, Any]:
    """Compile overall metrics and run the report aggregator."""
    from report.report_builder import build_report

    report_dict = build_report(state)
    return {"report": report_dict}
