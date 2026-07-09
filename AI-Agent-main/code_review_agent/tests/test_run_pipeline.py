import sys
import os
import json
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path
project_root = Path(__file__).parent.parent.resolve()
sys.path.append(str(project_root))

# Load keys
load_dotenv(project_root / ".env")

from agent.graph import review_graph
from report.report_to_pdf import generate_pdf_from_report

def main():
    # Use a small Python repository that has a unit test suite to verify tests & coverage
    repo_url = "https://github.com/pypa/sampleproject"
    print(f"[*] Starting manual end-to-end verification for repo: {repo_url}")
    print("[*] Google API Key:", os.getenv("GOOGLE_API_KEY")[:8] + "...")
    print("[*] E2B API Key:", os.getenv("E2B_API_KEY")[:8] + "...")
    
    inputs = {"repo_url": repo_url}
    config = {"recursion_limit": 50}
    
    print("[*] Streaming LangGraph workflow...")
    
    last_state = {}
    
    try:
        for event in review_graph.stream(inputs, config):
            for node_id, state_update in event.items():
                print(f"\n>>> NODE COMPLETED: {node_id}")
                last_state.update(state_update)
                
                if "errors" in state_update and state_update["errors"]:
                    print(f"    Errors: {state_update['errors']}")
                
                # Check progress indicators
                if node_id == "run_tests":
                    test_res = state_update.get("test_results", {})
                    print(f"    Test Suite Status: {test_res.get('status')} | Passed: {test_res.get('passed')}/{test_res.get('total')}")
                elif node_id == "generate_tests":
                    gen_tests = state_update.get("generated_tests", [])
                    print(f"    Generated Tests Count: {len(gen_tests)}")
                elif node_id == "validate_fixes":
                    val_res = state_update.get("validation_results", {})
                    print(f"    Fix Validation Status: {val_res.get('status')} | Passed: {val_res.get('passed')}/{val_res.get('total')}")
        
        # After completing, compile the PDF
        report = last_state.get("report")
        if not report:
            print("\n[-] Error: No report compiled in the final state.")
            return
            
        print("\n[+] Report Compiled. Attempting to generate PDF document...")
        
        output_pdf = project_root / "tests" / "verify_sampleproject_review.pdf"
        generate_pdf_from_report(report, str(output_pdf))
        
        print(f"\n[+] E2E VERIFICATION SUCCESSFUL!")
        print(f"[+] Output PDF review report saved to: {output_pdf}")
        
    except Exception as e:
        import traceback
        print(f"\n[-] E2E Verification failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
