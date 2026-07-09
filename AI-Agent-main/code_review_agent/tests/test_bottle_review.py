import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path
project_root = Path(__file__).parent.parent.resolve()
sys.path.append(str(project_root))

# Load keys
load_dotenv(project_root / ".env")

from agent.graph import review_graph

def main():
    repo_url = "https://github.com/bottlepy/bottle"
    print(f"[*] Starting manual review verification for repo: {repo_url}")
    print("[*] Google API Key is set:", bool(os.getenv("GOOGLE_API_KEY")))
    print("[*] E2B API Key is set:", bool(os.getenv("E2B_API_KEY")))
    
    inputs = {"repo_url": repo_url}
    config = {"recursion_limit": 50}
    
    print("[*] Streaming LangGraph nodes...")
    try:
        for event in review_graph.stream(inputs, config):
            for node_id, state_update in event.items():
                print(f"\n>>> NODE COMPLETED: {node_id}")
                if "errors" in state_update and state_update["errors"]:
                    print(f"    Errors: {state_update['errors']}")
                if "report" in state_update and state_update["report"]:
                    report = state_update["report"]
                    print("\n[+] Final Report Summary:")
                    print(report.get("summary", "No summary written."))
                    print("\n[+] Metrics:")
                    print(json.dumps(report.get("metrics", {}), indent=2))
        print("\n[+] Pipeline run completed successfully!")
    except Exception as e:
        import traceback
        print(f"\n[-] Pipeline run failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
