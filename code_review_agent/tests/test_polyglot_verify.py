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
    # Use Underscore JS repository to test JavaScript path detection and scanning
    repo_url = "https://github.com/jashkenas/underscore"
    print(f"[*] Starting polyglot verification for repository: {repo_url}")
    
    inputs = {"repo_url": repo_url}
    config = {"recursion_limit": 50}
    
    print("[*] Invoking LangGraph workflow...")
    try:
        # Run graph
        state_result = review_graph.invoke(inputs, config)
        
        print("\n[+] Verification Flow Completed!")
        print(f"    Detected Language: {state_result.get('language')}")
        print(f"    Files Read Count: {len(state_result.get('files', {}))}")
        print(f"    AST Chunks Count: {len(state_result.get('file_chunks', []))}")
        
        report = state_result.get("report", {})
        print("\n[+] Final Compiled Metrics:")
        print(json.dumps(report.get("metrics", {}), indent=2))
        
        print("\n[+] Lead Architect Summary:")
        print(report.get("summary", "No summary written."))
        
        # Verify language is detected as javascript
        if state_result.get("language") == "javascript":
            print("\n[🎉] SUCCESS: JavaScript repository detected and scanned correctly!")
        else:
            print("\n[❌] FAILURE: Repository language was not detected as JavaScript.")
            
    except Exception as e:
        import traceback
        print(f"\n[-] Verification failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
