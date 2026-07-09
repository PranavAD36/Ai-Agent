"""Pytest + coverage runner inside E2B sandbox.

Executes the target repo's test suite in a sandboxed environment
and collects pass/fail results and coverage metrics.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from sandbox.e2b_client import (
    create_sandbox,
    upload_repo_to_sandbox,
    install_dependencies,
    run_command_in_sandbox,
    cleanup_sandbox,
)

# Load environment variables
load_dotenv()


def run_tests_in_sandbox(repo_path: str, language: str = "python") -> dict[str, Any]:
    """Execute testing suite and coverage inside an isolated E2B sandbox."""
    
    if not os.getenv("E2B_API_KEY"):
        return {
            "status": "failed",
            "error": "E2B_API_KEY environment variable is not set",
            "passed": 0,
            "failed": 0,
            "total": 0,
            "has_tests": True
        }

    from tools.language_manager import get_language_config
    lang_config = get_language_config(language)

    print(f"[*] Provisioning E2B sandbox for testing...")
    sandbox = create_sandbox()
    
    try:
        # Upload repo contents to sandbox
        print(f"[*] Uploading files to E2B sandbox...")
        upload_repo_to_sandbox(sandbox, repo_path)
        
        # Determine install & test command
        command = lang_config["test_command"]
        
        if language.lower() == "python":
            local_req = Path(repo_path) / "requirements.txt"
            if local_req.exists():
                print(f"[*] Installing dependencies in sandbox...")
                install_dependencies(sandbox, "requirements.txt")
            else:
                # Install standard testing and utility dependencies
                print(f"[*] Installing pytest and common testing dependencies...")
                try:
                    sandbox.commands.run("pip install pytest pytest-cov requests urllib3 mock", cwd="/home/user/workspace")
                except Exception as e:
                    print(f"Warning: pytest/dependency installation failed: {e}")
        else:
            # For JavaScript, npm install is bundled in the test command, but let's log it
            print(f"[*] Running project install & test suite inside sandbox...")

        # Execute test suite with coverage configuration
        print(f"[*] Executing test suite in sandbox...")
        exec_result = run_command_in_sandbox(sandbox, command)
        
        stdout = exec_result.get("stdout", "")
        stderr = exec_result.get("stderr", "")
        exit_code = exec_result.get("exit_code", 1)
        
        # Parse pass/fail test results from raw output
        parsed_results = parse_test_results(stdout + "\n" + stderr)
        
        # Read the generated coverage file from sandbox
        coverage_report = {}
        cov_file_path = "/home/user/workspace/" + lang_config["coverage_file"]
        try:
            cov_content = sandbox.files.read(cov_file_path)
            if cov_content:
                coverage_report = json.loads(cov_content)
        except Exception as e:
            print(f"[*] Warning: Could not read coverage file {cov_file_path}: {e}")
            
        return {
            "status": "completed",
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "passed": parsed_results.get("passed", 0),
            "failed": parsed_results.get("failed", 0),
            "skipped": parsed_results.get("skipped", 0),
            "errors": parsed_results.get("errors", 0),
            "total": parsed_results.get("total", 0),
            "raw_summary": parsed_results.get("raw_summary", ""),
            "coverage": coverage_report
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "passed": 0,
            "failed": 0,
            "total": 0
        }
    finally:
        print(f"[*] Cleaning up E2B sandbox...")
        cleanup_sandbox(sandbox)


def parse_test_results(raw_output: str) -> dict[str, Any]:
    """Parse pytest or Jest summary lines using regex patterns."""
    
    summary = {
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "total": 0,
        "raw_summary": ""
    }
    
    lines = raw_output.splitlines()
    
    # 1. Try Pytest parser first
    summary_line = ""
    for line in reversed(lines):
        if line.startswith("=") and line.endswith("="):
            if any(word in line for word in ["passed", "failed", "error", "skipped"]):
                summary_line = line
                break
                
    if summary_line:
        summary["raw_summary"] = summary_line.strip("=")
        
        for key in ["passed", "failed", "skipped"]:
            match = re.search(r"(\d+)\s+" + re.escape(key), summary_line)
            if match:
                summary[key] = int(match.group(1))
                
        match_err = re.search(r"(\d+)\s+error", summary_line)
        if match_err:
            summary["errors"] = int(match_err.group(1))
            
        summary["total"] = (
            summary["passed"] + summary["failed"] + summary["skipped"] + summary["errors"]
        )
        return summary
        
    # 2. Try Jest parser
    jest_line = None
    for line in lines:
        if line.strip().startswith("Tests:"):
            jest_line = line.strip()
            break
            
    if jest_line:
        summary["raw_summary"] = jest_line
        passed_match = re.search(r"(\d+)\s+passed", jest_line)
        failed_match = re.search(r"(\d+)\s+failed", jest_line)
        skipped_match = re.search(r"(\d+)\s+skipped", jest_line)
        total_match = re.search(r"(\d+)\s+total", jest_line)
        
        if passed_match:
            summary["passed"] = int(passed_match.group(1))
        if failed_match:
            summary["failed"] = int(failed_match.group(1))
        if skipped_match:
            summary["skipped"] = int(skipped_match.group(1))
        if total_match:
            summary["total"] = int(total_match.group(1))
        else:
            summary["total"] = summary["passed"] + summary["failed"] + summary["skipped"]
            
        return summary
        
    return summary
