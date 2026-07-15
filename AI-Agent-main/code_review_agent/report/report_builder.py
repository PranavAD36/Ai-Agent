# """Assembles the final structured JSON review report.

# Combines static analysis results, LLM findings, suggested fixes,
# test results, and generated tests into a comprehensive report.
# """

# from __future__ import annotations

# import json
# import os
# from pathlib import Path
# from typing import Any

# from agent.prompts import CODE_REVIEW_SUMMARY_PROMPT


# def build_report(state: dict[str, Any]) -> dict[str, Any]:
#     """Compile code scan findings, E2B test validation telemetry, and AI summaries into a structured dictionary."""
    
#     # 1. Base Metrics
#     repo_url = state.get("repo_url", "")
#     repo_path = state.get("repo_path", "")
#     files = state.get("files", {})
#     file_chunks = state.get("file_chunks", [])
    
#     static_analysis = state.get("static_analysis_results", {})
#     findings = state.get("llm_findings", [])
#     suggested_fixes = state.get("suggested_fixes", [])
#     test_results = state.get("test_results", {})
#     generated_tests = state.get("generated_tests", [])
#     validation_results = state.get("validation_results", {})
    
#     # 2. Re-run sandbox test suite to get final coverage if new tests were generated
#     final_test_results = test_results
#     if generated_tests and repo_path:
#         print("[*] Re-running sandboxed test suite to compute final coverage statistics...")
#         try:
#             from tools.test_runner import run_tests_in_sandbox
#             final_res = run_tests_in_sandbox(repo_path, language=state.get("language", "python"))
#             if final_res.get("status") == "completed":
#                 final_test_results = final_res
#                 final_test_results["has_tests"] = True
#         except Exception as e:
#             print(f"[*] Warning: Could not run final validation suite: {e}")
            
#     # Calculate coverage percentages
#     initial_cov = 0.0
#     if "coverage" in test_results and "totals" in test_results["coverage"]:
#         initial_cov = test_results["coverage"]["totals"].get("percent_covered", 0.0)
        
#     final_cov = initial_cov
#     if "coverage" in final_test_results and "totals" in final_test_results["coverage"]:
#         final_cov = final_test_results["coverage"]["totals"].get("percent_covered", 0.0)
        
#     # 3. Request LLM Lead Architect Review Summary
#     from agent.llm import get_llm
#     llm = get_llm(temperature=0.1)
            
#     summary_text = "No LLM configuration available to write summary report."
#     if len(files) == 0:
#         summary_text = (
#             "## Code Review Summary: No Source Code Detected\n\n"
#             "**Status**: Completed (No Files Scanned)\n\n"
#             "No source code files matching the supported extensions (.py, .js, .jsx, .ts, .tsx) "
#             "were found in the repository. As a result, no static analysis, logic review, or "
#             "sandbox test executions could be performed. Please ensure the repository contains "
#             "supported source files and that the language configurations are correct."
#         )
#     elif llm:
#         print("[*] Generating Lead Architect overall review summary report...")
        
#         # Prepare readable findings string
#         cleaned_findings = []
#         for issue in findings:
#             if issue.get("status") == "identified":
#                 cleaned_findings.append(
#                     f"- {issue.get('severity', 'low').upper()}: {issue.get('symbol')} in {issue.get('file_path')} -> {issue.get('issue_description')}"
#                 )
#         findings_str = "\n".join(cleaned_findings) if cleaned_findings else "None identified."
        
#         prompt = CODE_REVIEW_SUMMARY_PROMPT.format(
#             files_reviewed=len(files),
#             total_issues=len(cleaned_findings),
#             test_status=final_test_results.get("status", "not_run"),
#             coverage_pct=f"{final_cov:.1f}",
#             findings=findings_str
#         )
        
#         import time
#         resp = None
#         for attempt in range(3):
#             try:
#                 resp = llm.invoke(prompt)
#                 break
#             except Exception as e:
#                 err_str = str(e).lower()
#                 if ("429" in err_str or "resource_exhausted" in err_str or "rate" in err_str) and attempt < 2:
#                     print(f"[*] LLM rate limit hit. Sleeping 15s before retrying summary generation (Attempt {attempt+1}/3)...")
#                     time.sleep(15)
#                 else:
#                     print(f"[*] Warning: Summary generation failed: {e}")
#                     summary_text = f"Review completed. Identified {len(cleaned_findings)} logic warnings. Final sandbox coverage at {final_cov:.1f}%."
#                     break
        
#         if resp:
#             summary_text = resp.content.strip()

#     report_dict = {
#         "repo_url": repo_url,
#         "repo_path": repo_path,
#         "metrics": {
#             "files_scanned": len(files),
#             "ast_chunks": len(file_chunks),
#             "findings_count": len([f for f in findings if f.get("status") == "identified"]),
#             "bandit_warnings": len(static_analysis.get("bandit", [])),
#             "pylint_warnings": len(static_analysis.get("pylint", [])),
#             "initial_coverage_pct": initial_cov,
#             "final_coverage_pct": final_cov,
#             "new_tests_generated": len(generated_tests)
#         },
#         "summary": summary_text,
#         "static_analysis": static_analysis,
#         "findings": findings,
#         "suggested_fixes": suggested_fixes,
#         "test_results": test_results,
#         "final_test_results": final_test_results,
#         "generated_tests": generated_tests,
#         "validation_results": validation_results
#     }
    
#     return report_dict


# def save_report_json(report: dict[str, Any], output_path: str) -> str:
#     """Save the report dictionary to a JSON file."""
#     path = Path(output_path).expanduser().resolve()
#     path.parent.mkdir(parents=True, exist_ok=True)
    
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(report, f, indent=4)
        
#     return str(path)
