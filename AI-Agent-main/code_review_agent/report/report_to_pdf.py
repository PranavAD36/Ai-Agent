# import re
# import datetime
# from pathlib import Path
# from fpdf import FPDF

# class ReviewReportPDF(FPDF):
#     def header(self):
#         if self.page_no() > 1:
#             self.set_font("helvetica", "I", 8)
#             self.set_text_color(100, 100, 100)
#             self.cell(0, 10, "Autonomous Code Review Agent - Scan Report", align="R", new_x="LMARGIN", new_y="NEXT")
#             self.set_draw_color(220, 220, 220)
#             self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
#             self.ln(5)

#     def footer(self):
#         self.set_y(-15)
#         self.set_font("helvetica", "I", 8)
#         self.set_text_color(120, 120, 120)
#         self.set_draw_color(230, 230, 230)
#         self.line(self.l_margin, self.get_y() - 2, self.w - self.r_margin, self.get_y() - 2)
#         page_str = f"Page {self.page_no()}/{{nb}}"
#         self.cell(0, 10, page_str, align="C")

# def clean_txt(text):
#     if not isinstance(text, str):
#         text = str(text)
#     replacements = {
#         '✅': '[Passed]',
#         '❌': '[Failed]',
#         '🔴': '[Critical]',
#         '🟠': '[High]',
#         '🟡': '[Medium]',
#         '🔵': '[Low]',
#         '⚪': '[Info]',
#         '🤖': 'Agent',
#         '🚀': 'Deploy',
#         '🛠️': 'Tools',
#         '📁': 'Dir',
#         '⚡': 'Quick',
#         '🔄': 'Workflow',
#         '\u2013': '-',
#         '\u2014': '-',
#         '\u2018': "'",
#         '\u2019': "'",
#         '\u201c': '"',
#         '\u201d': '"',
#         '\u2022': '*',
#         '\u2026': '...',
#         '\u2192': '->',
#     }
#     for symbol, replacement in replacements.items():
#         text = text.replace(symbol, replacement)
#     text = re.sub(r'[^\x00-\x7F]+', ' ', text)
#     return text.encode('latin-1', 'replace').decode('latin-1')

# def generate_pdf_from_report(report: dict, output_path: str):
#     pdf = ReviewReportPDF(orientation="P", unit="mm", format="A4")
#     pdf.set_auto_page_break(auto=True, margin=15)
#     pdf.alias_nb_pages()
    
#     PRIMARY_COLOR = (79, 70, 229)    # Deep Indigo (#4F46E5)
#     SECONDARY_COLOR = (6, 182, 212)  # Teal (#06B6D4)
#     TEXT_COLOR = (55, 65, 81)        # Charcoal (#374151)
#     CODE_BG = (243, 244, 246)        # Light Gray (#F3F4F6)
    
#     pdf.add_page()
    
#     # Title Cover
#     pdf.set_y(40)
#     pdf.set_font("helvetica", "B", 24)
#     pdf.set_text_color(*PRIMARY_COLOR)
#     pdf.multi_cell(0, 12, clean_txt("Autonomous Code Review\nDetailed Scan Report"), align="C", new_x="LMARGIN")
    
#     pdf.ln(8)
#     pdf.set_font("helvetica", "B", 12)
#     pdf.set_text_color(*SECONDARY_COLOR)
#     repo_url = report.get("repo_url", "Unknown Repository")
#     pdf.cell(0, 10, clean_txt(f"Repository: {repo_url}"), align="C", new_x="LMARGIN", new_y="NEXT")
    
#     pdf.ln(5)
#     pdf.set_draw_color(*PRIMARY_COLOR)
#     pdf.set_line_width(1.0)
#     pdf.line(30, pdf.get_y(), 180, pdf.get_y())
#     pdf.set_line_width(0.2)
    
#     pdf.ln(25)
#     pdf.set_font("helvetica", "", 10)
#     pdf.set_text_color(100, 100, 100)
#     timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
#     pdf.cell(0, 6, clean_txt(f"Generated on: {timestamp}"), align="C", new_x="LMARGIN", new_y="NEXT")
#     pdf.cell(0, 6, clean_txt("Audit Tool: Autonomous Code Review & Debugging Agent"), align="C", new_x="LMARGIN", new_y="NEXT")
    
#     # Page 2: Summary Metrics and Executive Summary
#     pdf.add_page()
#     pdf.set_text_color(*TEXT_COLOR)
    
#     pdf.set_font("helvetica", "B", 16)
#     pdf.set_text_color(*PRIMARY_COLOR)
#     pdf.cell(0, 10, "1. Executive Summary", new_x="LMARGIN", new_y="NEXT")
#     pdf.set_draw_color(*SECONDARY_COLOR)
#     pdf.line(pdf.get_x(), pdf.get_y() - 1, pdf.get_x() + 180, pdf.get_y() - 1)
#     pdf.ln(4)
    
#     # Render Summary
#     summary = report.get("summary", "No summary report compiled.")
#     pdf.set_font("helvetica", "", 10)
#     pdf.set_text_color(*TEXT_COLOR)
#     pdf.multi_cell(0, 5.5, clean_txt(summary), new_x="LMARGIN")
#     pdf.ln(6)
    
#     # Render Metrics Table
#     pdf.set_font("helvetica", "B", 12)
#     pdf.set_text_color(*SECONDARY_COLOR)
#     pdf.cell(0, 8, "Scan Metrics Table", new_x="LMARGIN", new_y="NEXT")
#     pdf.ln(2)
    
#     metrics = report.get("metrics", {})
#     metrics_data = [
#         ["Metric Name", "Value"],
#         ["Files Scanned", str(metrics.get("files_scanned", 0))],
#         ["AST Semantic Chunks", str(metrics.get("ast_chunks", 0))],
#         ["Security Warnings (Bandit)", str(metrics.get("bandit_warnings", 0))],
#         ["Code Quality Warnings (Pylint)", str(metrics.get("pylint_warnings", 0))],
#         ["Initial Coverage", f"{metrics.get('initial_coverage_pct', 0.0):.1f}%"],
#         ["Final Coverage", f"{metrics.get('final_coverage_pct', 0.0):.1f}%"],
#         ["New Tests Generated", str(metrics.get("new_tests_generated", 0))],
#         ["AI Findings Identified", str(metrics.get("findings_count", 0))]
#     ]
    
#     pdf.set_font("helvetica", "B", 9)
#     pdf.set_fill_color(240, 240, 255)
#     pdf.set_text_color(*PRIMARY_COLOR)
    
#     col_widths = [100, 80]
#     for row_idx, row in enumerate(metrics_data):
#         if row_idx == 0:
#             pdf.set_font("helvetica", "B", 9)
#             pdf.set_fill_color(240, 240, 255)
#             pdf.set_text_color(*PRIMARY_COLOR)
#         else:
#             pdf.set_font("helvetica", "", 9)
#             pdf.set_fill_color(255, 255, 255)
#             pdf.set_text_color(*TEXT_COLOR)
            
#         pdf.cell(col_widths[0], 7, clean_txt(row[0]), border=1, fill=True)
#         pdf.cell(col_widths[1], 7, clean_txt(row[1]), border=1, fill=True, align="C")
#         pdf.ln()
        
#     pdf.ln(8)
    
#     # Page 3: Static Analysis Warnings
#     pdf.add_page()
#     pdf.set_font("helvetica", "B", 16)
#     pdf.set_text_color(*PRIMARY_COLOR)
#     pdf.cell(0, 10, "2. Static Analysis Log", new_x="LMARGIN", new_y="NEXT")
#     pdf.set_draw_color(*SECONDARY_COLOR)
#     pdf.line(pdf.get_x(), pdf.get_y() - 1, pdf.get_x() + 180, pdf.get_y() - 1)
#     pdf.ln(4)
    
#     static_analysis = report.get("static_analysis", {})
#     bandit_issues = static_analysis.get("bandit", [])
#     pylint_issues = static_analysis.get("pylint", [])
    
#     pdf.set_font("helvetica", "B", 12)
#     pdf.set_text_color(*SECONDARY_COLOR)
#     pdf.cell(0, 8, f"Bandit Security Issues ({len(bandit_issues)} found)", new_x="LMARGIN", new_y="NEXT")
#     pdf.ln(2)
    
#     pdf.set_font("helvetica", "", 9)
#     pdf.set_text_color(*TEXT_COLOR)
#     if not bandit_issues:
#         pdf.cell(0, 6, "No security issues found by Bandit.", new_x="LMARGIN", new_y="NEXT")
#         pdf.ln(2)
#     else:
#         for idx, issue in enumerate(bandit_issues[:15]):
#             issue_text = f"{idx+1}. [{issue.get('issue_severity', 'LOW')}] {issue.get('issue_text')} in {issue.get('filename')}:L{issue.get('line_number')}"
#             pdf.multi_cell(0, 5, clean_txt(issue_text), new_x="LMARGIN")
#             pdf.ln(1)
            
#     pdf.ln(4)
#     pdf.set_font("helvetica", "B", 12)
#     pdf.set_text_color(*SECONDARY_COLOR)
#     pdf.cell(0, 8, f"Pylint Quality & Style Warnings ({len(pylint_issues)} found)", new_x="LMARGIN", new_y="NEXT")
#     pdf.ln(2)
    
#     pdf.set_font("helvetica", "", 9)
#     pdf.set_text_color(*TEXT_COLOR)
#     if not pylint_issues:
#         pdf.cell(0, 6, "No code quality warnings found by Pylint.", new_x="LMARGIN", new_y="NEXT")
#         pdf.ln(2)
#     else:
#         for idx, issue in enumerate(pylint_issues[:20]):
#             issue_text = f"{idx+1}. [{issue.get('type', 'warning')}] {issue.get('message')} ({issue.get('symbol')}) in {issue.get('path')}:L{issue.get('line')}"
#             pdf.multi_cell(0, 5, clean_txt(issue_text), new_x="LMARGIN")
#             pdf.ln(1)
            
#     # Page 4: AI Findings & Code Fixes
#     pdf.add_page()
#     pdf.set_font("helvetica", "B", 16)
#     pdf.set_text_color(*PRIMARY_COLOR)
#     pdf.cell(0, 10, "3. AI Logic Findings & Code Fixes", new_x="LMARGIN", new_y="NEXT")
#     pdf.set_draw_color(*SECONDARY_COLOR)
#     pdf.line(pdf.get_x(), pdf.get_y() - 1, pdf.get_x() + 180, pdf.get_y() - 1)
#     pdf.ln(4)
    
#     findings = report.get("findings", [])
#     suggested_fixes = report.get("suggested_fixes", [])
    
#     pdf.set_font("helvetica", "B", 12)
#     pdf.set_text_color(*SECONDARY_COLOR)
#     pdf.cell(0, 8, f"Identified AI Logic Findings ({len(findings)} found)", new_x="LMARGIN", new_y="NEXT")
#     pdf.ln(2)
    
#     if not findings:
#         pdf.set_font("helvetica", "", 9)
#         pdf.set_text_color(*TEXT_COLOR)
#         pdf.cell(0, 6, "No logical bugs identified by the AI.", new_x="LMARGIN", new_y="NEXT")
#         pdf.ln(2)
#     else:
#         for idx, finding in enumerate(findings):
#             if finding.get("status") == "identified":
#                 pdf.set_font("helvetica", "B", 10)
#                 pdf.set_text_color(220, 53, 69)
#                 title = f"{idx+1}. {finding.get('severity', 'low').upper()}: {finding.get('symbol')} in {finding.get('file_path')}"
#                 pdf.cell(0, 6, clean_txt(title), new_x="LMARGIN", new_y="NEXT")
                
#                 pdf.set_font("helvetica", "", 9)
#                 pdf.set_text_color(*TEXT_COLOR)
#                 pdf.multi_cell(0, 5, clean_txt(f"Issue: {finding.get('issue_description')}"), new_x="LMARGIN")
#                 pdf.multi_cell(0, 5, clean_txt(f"Suggested Fix: {finding.get('suggested_fix')}"), new_x="LMARGIN")
#                 pdf.ln(2)

                
#     pdf.ln(4)
#     pdf.set_font("helvetica", "B", 12)
#     pdf.set_text_color(*SECONDARY_COLOR)
#     pdf.cell(0, 8, f"Proposed and Validated Fixes ({len(suggested_fixes)} generated)", new_x="LMARGIN", new_y="NEXT")
#     pdf.ln(2)
    
#     if not suggested_fixes:
#         pdf.set_font("helvetica", "", 9)
#         pdf.set_text_color(*TEXT_COLOR)
#         pdf.cell(0, 6, "No proposed fixes applied.", new_x="LMARGIN", new_y="NEXT")
#         pdf.ln(2)
#     else:
#         for idx, fix in enumerate(suggested_fixes):
#             pdf.set_font("helvetica", "B", 10)
#             pdf.set_text_color(40, 167, 69)
#             pdf.cell(0, 6, clean_txt(f"Fix {idx+1}: {fix.get('symbol')} in {fix.get('file_path')}"), new_x="LMARGIN", new_y="NEXT")
            
#             pdf.set_font("helvetica", "", 9)
#             pdf.set_text_color(*TEXT_COLOR)
#             pdf.multi_cell(0, 5, clean_txt(f"Explanation: {fix.get('explanation')}"), new_x="LMARGIN")
#             pdf.ln(2)
            
#     # Page 5: Sandbox Test Results and Generated Tests
#     pdf.add_page()
#     pdf.set_font("helvetica", "B", 16)
#     pdf.set_text_color(*PRIMARY_COLOR)
#     pdf.cell(0, 10, "4. Sandbox Test Results & Telemetry", new_x="LMARGIN", new_y="NEXT")
#     pdf.set_draw_color(*SECONDARY_COLOR)
#     pdf.line(pdf.get_x(), pdf.get_y() - 1, pdf.get_x() + 180, pdf.get_y() - 1)
#     pdf.ln(4)
    
#     generated_tests = report.get("generated_tests", [])
    
#     pdf.set_font("helvetica", "B", 12)
#     pdf.set_text_color(*SECONDARY_COLOR)
#     pdf.cell(0, 8, "Base Sandbox Unit Testing", new_x="LMARGIN", new_y="NEXT")
#     pdf.ln(2)
    
#     test_results = report.get("final_test_results", report.get("test_results", {}))
#     test_status = test_results.get("status", "not_run")
    
#     pdf.set_font("helvetica", "", 9)
#     pdf.set_text_color(*TEXT_COLOR)
#     if test_status == "no_tests_found":
#         pdf.multi_cell(0, 5, "No test suite detected in this repository. Adding unit tests under 'tests/' is recommended.", new_x="LMARGIN")
#     elif test_status == "completed":
#         pdf.multi_cell(0, 5, clean_txt(f"Test Status: COMPLETED"), new_x="LMARGIN")
#         pdf.multi_cell(0, 5, clean_txt(f"Passed Tests: {test_results.get('passed', 0)} / {test_results.get('total', 0)}"), new_x="LMARGIN")
#         pdf.multi_cell(0, 5, clean_txt(f"Pytest Summary: {test_results.get('raw_summary', '')}"), new_x="LMARGIN")
#     else:
#         pdf.multi_cell(0, 5, clean_txt(f"Test Status: FAILED or ERROR ({test_results.get('error', 'Unknown Error')})"), new_x="LMARGIN")
        
#     pdf.ln(4)
#     pdf.set_font("helvetica", "B", 12)
#     pdf.set_text_color(*SECONDARY_COLOR)
#     pdf.cell(0, 8, f"AI-Generated Unit Tests ({len(generated_tests)} written)", new_x="LMARGIN", new_y="NEXT")
#     pdf.ln(2)
    
#     if not generated_tests:
#         pdf.set_font("helvetica", "", 9)
#         pdf.set_text_color(*TEXT_COLOR)
#         pdf.cell(0, 6, "No new unit tests were generated.", new_x="LMARGIN", new_y="NEXT")
#     else:
#         for idx, t in enumerate(generated_tests):
#             pdf.set_font("helvetica", "B", 10)
#             pdf.set_text_color(*PRIMARY_COLOR)
#             pdf.cell(0, 6, clean_txt(f"Test {idx+1}: {t.get('file_path')}"), new_x="LMARGIN", new_y="NEXT")
            
#             pdf.set_font("helvetica", "", 9)
#             pdf.set_text_color(*TEXT_COLOR)
#             pdf.cell(0, 5, clean_txt(f"Target Function: {t.get('function_name')} in {t.get('target_file')}"), new_x="LMARGIN", new_y="NEXT")
#             pdf.cell(0, 5, clean_txt(f"Validation Status: {t.get('status')}"), new_x="LMARGIN", new_y="NEXT")
            
#             pdf.ln(2)
#             test_code = t.get("test_code", "")
#             lines = test_code.splitlines()[:12]
#             truncated_code = "\n".join(lines)
#             if len(lines) > 12:
#                 truncated_code += "\n# ... (truncated)"
            
#             pdf.set_font("courier", "", 8)
#             pdf.set_text_color(50, 50, 50)
#             pdf.set_fill_color(*CODE_BG)
#             pdf.multi_cell(0, 4, clean_txt(truncated_code), border=1, fill=True, new_x="LMARGIN")
#             pdf.ln(4)
            
#     pdf.output(output_path)
