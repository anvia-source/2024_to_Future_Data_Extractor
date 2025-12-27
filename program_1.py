import fitz  # PyMuPDF
import pdfplumber
import re
from datetime import datetime
import logging
import pandas as pd
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_headnotes(pdf_path):
    text = ""
    # Extract all text from PDF
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += "\n" + page_text
    
    headnotes_list = []
    
    # 1️⃣ Primary pattern: Ends at "Case Law Cited" or "List of Citations and Other References"
    headnotes_pattern = re.compile(
        r"(Headnotes(?:†)?\s*[\n\r]+)(.*?)(?=(Case Law Cited|List of Citations and Other References))",
        re.DOTALL | re.IGNORECASE
    )
    matches = headnotes_pattern.findall(text)
    
    # 2️⃣ Fallback pattern: Ends at "List of Acts"
    if not matches:
        fallback_pattern = re.compile(
            r"(Headnotes(?:†)?\s*[\n\r]+)(.*?)(?=(List of Acts))",
            re.DOTALL | re.IGNORECASE
        )
        matches = fallback_pattern.findall(text)
    
    # Store headnotes
    for match in matches:
        title = match[0].strip()
        content = match[1].strip()
        headnotes_list.append({
            "title": title,
            "content": content
        })
    
    # 3️⃣ New section: Issue for Consideration → Headnotes
    issue_pattern = re.compile(
        r"(Issue\s+for\s+Consideration\s*[\n\r]+)(.*?)(?=(Headnotes))",
        re.DOTALL | re.IGNORECASE
    )
    issue_matches = issue_pattern.findall(text)
    
    for match in issue_matches:
        new_title = match[0].strip()
        new_content = match[1].strip()
        headnotes_list.append({
            "title": new_title,
            "content": new_content
        })
    
    return headnotes_list

def extract_legal_details(pdf_path: str) -> dict:
    try:
        doc = fitz.open(pdf_path)
        # Store the total page count
        total_pages = len(doc)
        first_page_text = doc[0].get_text()
        all_text = "".join([page.get_text() for page in doc])
        type_text = (doc[0].get_text() + doc[1].get_text()) if len(doc) > 1 else doc[0].get_text()

        # --- Case Title (Cleaned, Handle No Vs/v) ---
        title_match = re.search(r'([^\n]+?)\s+v\.?\s+([^\n\(]+)', first_page_text, re.IGNORECASE)
        if title_match:
            raw_title = f"{title_match.group(1).strip()} v. {title_match.group(2).strip()}"
            case_title = re.sub(r'\(.*?\)$', '', raw_title).strip()
        else:
            # Fallback: Extract first three lines from first page
            lines = [line.strip() for line in first_page_text.splitlines() if line.strip()][:3]
            if lines:
                # Combine first three lines and clean annotations
                combined_lines = " ".join(lines)
                # Remove annotations like [2024] 10 S.C.R. 961 : 2024 INSC 789
                case_title = re.sub(r'\[\d{4}\]\s+\d+\s+S\.C\.R\.\s+\d+\s*:\s*\d+\s+INSC\s+\d+', '', combined_lines).strip()
                # Further clean extra spaces and parentheses
                case_title = re.sub(r'\s+', ' ', case_title).strip()
                case_title = re.sub(r'\(.*?\)$', '', case_title).strip()
            else:
                case_title = "Not found"

        # --- Case Numbers (First Page Only, Cleaned, Deduplicated) ---
        case_patterns = [
            r'(?:[\)\(]?\s*)?(?:Nos\.?|No\.?|Number)?\s*([A-Za-z\s]*?(?:C\.A\.|Cr\.A\.|Civil Appeal|Criminal Appeal|Writ Petition|SLP|Review Petition)?\s*\d+(?:[-–/]\d+)?\s*(?:of|\/)\s*\d{4})'
        ]

        case_nos_raw = []
        for pattern in case_patterns:
            matches = re.findall(pattern, first_page_text, re.IGNORECASE)
            case_nos_raw.extend([m.strip() for m in matches])

        cleaned_case_nos = []
        for cn in case_nos_raw:
            if all(cn not in existing and existing not in cn for existing in cleaned_case_nos):
                cleaned_case_nos.append(cn)

        case_no = cleaned_case_nos[0] if cleaned_case_nos else "Not found"
        other_case_nos = ", ".join(cleaned_case_nos[1:]) if len(cleaned_case_nos) > 1 else "Not found"

        # --- Judgment Date ---
        date_patterns = [
            r'\b(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})\b',
            r'\b([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4})\b',
            r'\b(\d{1,2}\s+[A-Za-z]+\s+\d{4})\b',
            r'\b([A-Za-z]+\s+\d{4})\b',
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b',
            r'\b(\d{1,2}\s+[A-Za-z]{3,}\s+\d{4})\b',
            r'\b(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\b',
            r'\b([A-Za-z]{3,}\s+\d{1,2}(?:st|nd|rd|th)?\s+\d{4})\b',
            r'\b(?:\d{1,2}(?:st|nd|rd|th)?\s+day\s+of\s+([A-Za-z]+)\s*,\s*(\d{4}))\b',
            r'\b(?:[A-Za-z]+\s+day\s+of\s+([A-Za-z]+)\s*,\s*(\d{4}))\b'
        ]
        judgement_date = month = year = "Not found"
        for pattern in date_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                if match.lastindex == 1:
                    date_str = match.group(1).replace(",", "").strip()
                else:
                    date_str = f"{match.group(1)} {match.group(2)}".replace(",", "").strip()

                month_abbr = {
                    'jan': 'January', 'feb': 'February', 'mar': 'March', 'apr': 'April',
                    'may': 'May', 'jun': 'June', 'jul': 'July', 'aug': 'August',
                    'sep': 'September', 'oct': 'October', 'nov': 'November', 'dec': 'December'
                }
                for abbr, full in month_abbr.items():
                    date_str = re.sub(rf'\b{abbr}\b', full, date_str, flags=re.IGNORECASE)
                for fmt in [
                    "%d %B %Y", "%B %d %Y", "%B %Y", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%B %d%Y"
                ]:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        judgement_date = dt.strftime("%d-%m-%Y") if fmt != "%B %Y" else f"01-{dt.strftime('%m-%Y')}"
                        month = dt.strftime("%B")
                        year = dt.strftime("%Y")
                        break
                    except ValueError:
                        continue
                if judgement_date != "Not found":
                    break

        # --- Extract Headnotes ---
        headnotes_data = extract_headnotes(pdf_path)
        
        # Process headnotes data
        headnotes_content = ""
        headnote_extraction_method = "Not found"
        
        if headnotes_data:
            # Combine all headnotes content
            all_headnotes = []
            for hn in headnotes_data:
                if hn['title'] and hn['content']:
                    all_headnotes.append(f"{hn['title']}: {hn['content']}")
                elif hn['content']:
                    all_headnotes.append(hn['content'])
            
            headnotes_content = " | ".join(all_headnotes)
            headnote_extraction_method = "PDF Plumber Pattern Matching"
        
        if not headnotes_content:
            headnotes_content = "Not found"
            headnote_extraction_method = "None"
        
        # Split headnotes if too long
        headnotes_part1 = headnotes_content
        headnotes_part2 = ""
        max_cell_length = 32767  # Excel cell limit
        if len(headnotes_content) > max_cell_length:
            headnotes_part1 = headnotes_content[:max_cell_length]
            headnotes_part2 = headnotes_content[max_cell_length:]

        # --- Document Type Detection ---
        lines = type_text.splitlines()
        doc_type = "Judgment"  # Default
        for i, line in enumerate(lines):
            if "judgment / order of the supreme court" in line.lower():
                for j in range(1, 3):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip().lower()
                        if "order" == next_line or next_line.startswith("order"):
                            doc_type = "Order"
                            break
                break

        # --- Judge Names & No. of Judges ---
        judge_names = []
        judge_text = "".join([doc[i].get_text() for i in range(min(3, len(doc)))])
        match = re.search(r'\[([\w\s\.\*&\-\,]+(?:\s+and\s+[\w\s\.\*&\-]+)?)\s*,?\s*(?:J\.J\.|J\.|CJI)\s*\]', judge_text, re.IGNORECASE)

        if match:
            raw_judges = match.group(1)
            judge_parts = re.split(r'\s+and\s+|,', raw_judges)
            for name in judge_parts:
                clean_name = name.strip()
                # Exclude judge suffixes
                if clean_name and clean_name.upper() not in ["J", "JJ", "CJI"] and clean_name not in judge_names:
                    judge_names.append(clean_name)

        no_of_judges = len(judge_names)

        result = {
            "Case No. (Program 1)": case_no,
            "Other Case Nos (Program 1)": other_case_nos,
            "Case Title (Program 1)": case_title,
            "Judgment Date (Program 1)": judgement_date,
            "Month (Program 1)": month,
            "Year (Program 1)": year,
            "Headnotes (Program 1)": headnotes_part1,
            "Headnote Extraction Method (Program 1)": headnote_extraction_method,
            "Type (Program 1)": doc_type,
            "Judge Names (Program 1)": ", ".join(judge_names) if judge_names else "Not found",
            "No. of Judges (Program 1)": str(no_of_judges) if no_of_judges > 0 else "Not found",
            "Page Count (Program 1)": str(total_pages)
        }
        
        if headnotes_part2:
            result["Headnotes_1 (Program 1)"] = headnotes_part2
        else:
            result["Headnotes_1 (Program 1)"] = ""

        return result
    except Exception as e:
        logger.error(f"Error in Program 1 for {pdf_path}: {str(e)}")
        return {"Error (Program 1)": str(e)}

# Export to Excel (append mode)
def export_to_excel(data: dict, output_path: str):
    try:
        # Convert dictionary to DataFrame
        df = pd.DataFrame([data])
        
        # Check if Excel file exists
        if os.path.exists(output_path):
            # Read existing Excel file
            existing_df = pd.read_excel(output_path)
            # Ensure required columns exist in existing_df
            required_columns = [
                'Page Count (Program 1)',
                'Headnote Extraction Method (Program 1)',
                'Headnotes_1 (Program 1)'
            ]
            for col in required_columns:
                if col not in existing_df.columns:
                    if col == 'Headnotes_1 (Program 1)':
                        existing_df[col] = ''
                    else:
                        existing_df[col] = 'Not recorded'
            # Append new data
            df = pd.concat([existing_df, df], ignore_index=True)
        # Write to Excel
        df.to_excel(output_path, index=False)
        logger.info(f"Data appended to {output_path}")
    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")

