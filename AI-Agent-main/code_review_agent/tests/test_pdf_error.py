import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from report.report_to_pdf import generate_pdf_from_report

def main():
    history_file = Path(__file__).parent.parent / "report" / "history.json"
    if not history_file.exists():
        print("History file not found.")
        return
        
    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)
        
    if not history:
        print("History is empty.")
        return
        
    # Get the latest report
    latest_item = history[0]
    report = latest_item.get("report")
    
    print("Attempting to generate PDF report...")
    output_pdf = Path(__file__).parent / "test_output.pdf"
    
    try:
        generate_pdf_from_report(report, str(output_pdf))
        print("PDF generated successfully!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Find where it crashed in findings
        findings = report.get("findings", [])
        print("\n=== DEBUG STATE ===")
        print("Total findings:", len(findings))
        for idx, finding in enumerate(findings):
            print(f"\nFinding {idx+1}:")
            print("  Symbol:", finding.get("symbol"))
            print("  File:", finding.get("file_path"))
            print("  Severity:", finding.get("severity"))
            print("  Issue:", repr(finding.get("issue_description")))
            print("  Suggested Fix:", repr(finding.get("suggested_fix")))


if __name__ == "__main__":
    main()
