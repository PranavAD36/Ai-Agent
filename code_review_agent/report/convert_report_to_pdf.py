import os
import re
from pathlib import Path
from fpdf import FPDF

class CustomPDF(FPDF):
    def header(self):
        # Top margin header (only after page 1)
        if self.page_no() > 1:
            self.set_font("helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, "Autonomous Code Review & Debugging Agent - Weeks 1-4 Report", align="R", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(220, 220, 220)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(5)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        
        # Draw top divider
        self.set_draw_color(230, 230, 230)
        self.line(self.l_margin, self.get_y() - 2, self.w - self.r_margin, self.get_y() - 2)
        
        # Page numbers
        page_str = f"Page {self.page_no()}/{{nb}}"
        self.cell(0, 10, page_str, align="C")

def clean_txt(text):
    # Replacements for common unicode characters that cause issues with latin-1
    text = text.replace('\u2013', '-')  # en-dash
    text = text.replace('\u2014', '-')  # em-dash
    text = text.replace('\u2018', "'")  # curly single quote left
    text = text.replace('\u2019', "'")  # curly single quote right
    text = text.replace('\u201c', '"')  # curly double quote left
    text = text.replace('\u201d', '"')  # curly double quote right
    text = text.replace('\u2022', '*')  # standard bullet point
    text = text.replace('\u2026', '...') # ellipsis
    text = text.replace('\u2192', '->')  # arrow
    # Safe encoding to latin-1
    return text.encode('latin-1', 'replace').decode('latin-1')

def parse_markdown_to_pdf(md_path, pdf_path):
    pdf = CustomPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages()
    
    # Define Color Palette
    PRIMARY_COLOR = (79, 70, 229)    # Deep Indigo (#4F46E5)
    SECONDARY_COLOR = (6, 182, 212)  # Teal (#06B6D4)
    TEXT_COLOR = (55, 65, 81)        # Charcoal (#374151)
    CODE_BG = (243, 244, 246)        # Light Gray (#F3F4F6)
    
    # Read Markdown
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    pdf.add_page()
    
    # --- RENDER COVER/TITLE AREA ---
    pdf.set_y(40)
    pdf.set_font("helvetica", "B", 26)
    pdf.set_text_color(*PRIMARY_COLOR)
    pdf.multi_cell(0, 12, clean_txt("Autonomous Code Review &\nDebugging Agent"), align="C")
    
    pdf.ln(8)
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(*SECONDARY_COLOR)
    pdf.cell(0, 10, clean_txt("Comprehensive Weeks 1-4 Progress & Technical Explanation Report"), align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.set_draw_color(*PRIMARY_COLOR)
    pdf.set_line_width(1.0)
    pdf.line(40, pdf.get_y(), 170, pdf.get_y())
    pdf.set_line_width(0.2) # reset
    
    pdf.ln(25)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, clean_txt("ABM Internship - Project 4 Milestone"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, clean_txt("Technology: LangGraph, E2B Sandbox, Gemini & Llama-3.3"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, clean_txt("Report Compiled: June 2026"), align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.add_page()
    
    # Reset default text state
    pdf.set_text_color(*TEXT_COLOR)
    
    # Parse Markdown lines
    in_code_block = False
    code_text = []
    
    in_table = False
    table_headers = []
    table_rows = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # --- Handle Code Blocks ---
        if stripped.startswith("```"):
            if in_code_block:
                in_code_block = False
                # Write Code Block
                pdf.set_font("courier", "", 9)
                pdf.set_text_color(50, 50, 50)
                pdf.set_fill_color(*CODE_BG)
                
                # Join code block lines
                full_code = "".join(code_text)
                full_code = clean_txt(full_code)
                
                # Check height first to avoid page-break splits in background rect
                line_count = len(code_text)
                required_h = line_count * 5 + 6
                if pdf.get_y() + required_h > pdf.page_break_trigger:
                    pdf.add_page()
                    
                pdf.multi_cell(0, 5, full_code, border=1, fill=True)
                pdf.ln(4)
                code_text = []
            else:
                in_code_block = True
            i += 1
            continue
            
        if in_code_block:
            code_text.append(line)
            i += 1
            continue
            
        # --- Handle Tables ---
        if stripped.startswith("|"):
            in_table = True
            # Parse table row
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            
            # Check if this is a separator line (e.g. | :--- | :--- |)
            if all(re.match(r"^:?-+:?$", c) for c in cells):
                i += 1
                continue
                
            if not table_headers:
                table_headers = cells
            else:
                table_rows.append(cells)
                
            i += 1
            continue
        elif in_table and not stripped.startswith("|"):
            # Table ended, render it
            in_table = False
            
            # Draw Table
            pdf.set_font("helvetica", "B", 9)
            pdf.set_fill_color(240, 240, 255)
            pdf.set_text_color(*PRIMARY_COLOR)
            
            # Determine widths
            col_widths = []
            num_cols = len(table_headers)
            if num_cols == 3:
                col_widths = [45, 65, 80] # Custom fit for Tech Stack table
            else:
                col_widths = [190 / num_cols] * num_cols
                
            # Header Row
            for col_idx, header_text in enumerate(table_headers):
                pdf.cell(col_widths[col_idx], 8, clean_txt(header_text), border=1, fill=True, align="C")
            pdf.ln()
            
            # Content Rows
            pdf.set_font("helvetica", "", 8)
            pdf.set_text_color(*TEXT_COLOR)
            fill_toggle = False
            
            for row in table_rows:
                # Row height check
                row_h = 6
                # Calculate max height needed for row based on wrap
                max_lines = 1
                for col_idx, cell_text in enumerate(row):
                    line_w = col_widths[col_idx] - 2
                    # Approximate lines needed
                    text_len = len(cell_text)
                    approx_chars_per_line = line_w * 1.5
                    lines_needed = max(1, int(text_len / approx_chars_per_line) + 1)
                    max_lines = max(max_lines, lines_needed)
                
                calculated_h = max_lines * 4.5
                if pdf.get_y() + calculated_h > pdf.page_break_trigger:
                    pdf.add_page()
                    # Re-draw headers on new page
                    pdf.set_font("helvetica", "B", 9)
                    pdf.set_fill_color(240, 240, 255)
                    pdf.set_text_color(*PRIMARY_COLOR)
                    for col_idx, header_text in enumerate(table_headers):
                        pdf.cell(col_widths[col_idx], 8, clean_txt(header_text), border=1, fill=True, align="C")
                    pdf.ln()
                    pdf.set_font("helvetica", "", 8)
                    pdf.set_text_color(*TEXT_COLOR)
                
                pdf.set_fill_color(252, 252, 254) if fill_toggle else pdf.set_fill_color(255, 255, 255)
                fill_toggle = not fill_toggle
                
                x_before = pdf.get_x()
                y_before = pdf.get_y()
                
                max_y_after = y_before
                
                for col_idx, cell_text in enumerate(row):
                    pdf.set_xy(x_before + sum(col_widths[:col_idx]), y_before)
                    pdf.multi_cell(col_widths[col_idx], 5, clean_txt(cell_text), border=1, fill=True)
                    max_y_after = max(max_y_after, pdf.get_y())
                
                pdf.set_xy(x_before, max_y_after)
                
            pdf.ln(5)
            table_headers = []
            table_rows = []
            
        # --- Handle Headers ---
        if stripped.startswith("#"):
            # Check hierarchy
            header_level = len(re.match(r"^#+", stripped).group())
            header_text = stripped.lstrip("#").strip()
            header_text = clean_txt(header_text)
            
            if header_level == 1:
                pdf.ln(8)
                pdf.set_font("helvetica", "B", 18)
                pdf.set_text_color(*PRIMARY_COLOR)
                pdf.cell(0, 12, header_text, new_x="LMARGIN", new_y="NEXT")
                # Draw underline
                pdf.set_draw_color(*SECONDARY_COLOR)
                pdf.line(pdf.get_x(), pdf.get_y() - 1, pdf.get_x() + 190, pdf.get_y() - 1)
                pdf.ln(4)
            elif header_level == 2:
                pdf.ln(6)
                pdf.set_font("helvetica", "B", 14)
                pdf.set_text_color(*SECONDARY_COLOR)
                pdf.cell(0, 10, header_text, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
            elif header_level == 3:
                pdf.ln(4)
                pdf.set_font("helvetica", "B", 11)
                pdf.set_text_color(40, 50, 70)
                pdf.cell(0, 8, header_text, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(1)
            i += 1
            continue
            
        # --- Handle Bullet Lists ---
        if stripped.startswith("*") or stripped.startswith("-"):
            bullet_text = stripped[1:].strip()
            
            # Clean markdown bold/code markers
            bullet_text = re.sub(r"\*\*([^*]+)\*\*", r"\1", bullet_text)
            bullet_text = re.sub(r"`([^`]+)`", r"\1", bullet_text)
            bullet_text = clean_txt(bullet_text)
            
            # Bullet indent
            pdf.set_x(pdf.get_x() + 5)
            pdf.set_font("helvetica", "B", 10)
            pdf.set_text_color(*PRIMARY_COLOR)
            pdf.cell(4, 6, "-") # Bullet character replaced with safe "-" dash
            
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(*TEXT_COLOR)
            pdf.multi_cell(0, 6, bullet_text)
            pdf.set_x(pdf.l_margin) # Restore indent
            i += 1
            continue
            
        # --- Handle Paragraph Text ---
        if stripped:
            # Clean markdown formatting
            clean_line = re.sub(r"\*\*([^*]+)\*\*", r"\1", stripped)
            clean_line = re.sub(r"`([^`]+)`", r"\1", clean_line)
            
            # Clean up markdown links [text](url) -> text (url)
            clean_line = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", clean_line)
            clean_line = clean_txt(clean_line)
            
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(*TEXT_COLOR)
            pdf.multi_cell(0, 6, clean_line)
            pdf.ln(3)
        else:
            # Empty line spacer
            pdf.ln(2)
            
        i += 1
        
    # Output PDF
    pdf.output(pdf_path)
    print(f"[+] PDF generated successfully at: {pdf_path}")

if __name__ == "__main__":
    current_dir = Path(__file__).parent.resolve()
    # Workspace root
    root_dir = current_dir.parent.parent.parent
    md_file = root_dir / "comprehensive_weeks_1_4_report.md"
    pdf_file = root_dir / "comprehensive_weeks_1_4_report.pdf"
    
    if md_file.exists():
        parse_markdown_to_pdf(str(md_file), str(pdf_file))
    else:
        # Check in local workspace folder
        local_md = Path("m:/FOR ME/M/COLLEGE WORK/ABM Internship/INTERN PROJECT/comprehensive_weeks_1_4_report.md")
        local_pdf = Path("m:/FOR ME/M/COLLEGE WORK/ABM Internship/INTERN PROJECT/comprehensive_weeks_1_4_report.pdf")
        if local_md.exists():
            parse_markdown_to_pdf(str(local_md), str(local_pdf))
        else:
            print("[-] Error: comprehensive_weeks_1_4_report.md not found.")
