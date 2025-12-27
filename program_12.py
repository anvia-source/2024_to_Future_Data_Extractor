import logging
import pdfplumber
import re
import pandas as pd
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Extract text from each page of the PDF
def extract_text_by_page(pdf_path: str) -> list:
    try:
        pages_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                pages_text.append(page_text.strip())
        if not pages_text or all(not page for page in pages_text):
            logger.warning(f"No text extracted from PDF {pdf_path}.")
            return []
        logger.info(f"Extracted text from {len(pages_text)} pages in PDF {pdf_path}.")
        return pages_text
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
        return []

# Split text into paragraphs
def split_into_paragraphs(text: str) -> list:
    if not text or text.strip() == "":
        return []
    paragraphs = re.split(
        r'(?:\n\s*(\d+\.\s+))|(?:\n{2,})|(?=(?:Judgment|Conclusion|Appearances|Facts|Background|Issue)\b)',
        text
    )
    return [p.strip() for p in paragraphs if p and p.strip()]

# Extract conclusion
def extract_conclusion(pages_text: list) -> str:
    conclusion = "Not Found"
    total_pages = len(pages_text)

    conclusion_patterns = [
        r"Conclusion\b",
        r"Conclusions\b",
        r"OUR CONCLUSION\b",
        r"Final Remarks\b",
        r"Summary of Findings\b",
        r"Judgment Summary\b",
        r"Concluding Remarks\b"
    ]

    conclusion_found = False
    for page_idx in range(total_pages - 1, -1, -1):
        page_text = pages_text[page_idx]
        paragraphs = split_into_paragraphs(page_text)
        for i, para in enumerate(paragraphs):
            for pat in conclusion_patterns:
                if re.search(pat, para, re.IGNORECASE):
                    conclusion_text = para
                    for j in range(i + 1, len(paragraphs)):
                        conclusion_text += "\n" + paragraphs[j]
                    if page_idx == total_pages - 1:
                        conclusion = conclusion_text
                        conclusion_found = True
                        break
                    for next_page_idx in range(page_idx + 1, total_pages):
                        next_page_text = pages_text[next_page_idx]
                        conclusion_text += "\n" + next_page_text
                    conclusion = conclusion_text
                    conclusion_found = True
                    break
            if conclusion_found:
                break
        if conclusion_found:
            break

    if not conclusion_found:
        conclusion = ""
        if total_pages >= 2:
            conclusion = pages_text[-2] + "\n" + pages_text[-1]
            logger.info(f"No Conclusion section found. Extracted last two pages: {conclusion[:100]}...")
        elif total_pages == 1:
            conclusion = pages_text[-1]
            logger.info(f"No Conclusion section found. Extracted single page: {conclusion[:100]}...")
        else:
            conclusion = "Not Found"

    return conclusion

# Main extraction function
def extract_case_details(pdf_path: str) -> dict:
    try:
        pages_text = extract_text_by_page(pdf_path)
        if not pages_text:
            return {"Error (Program 12)": "No text extracted from PDF"}

        # Extract conclusion
        conclusion = extract_conclusion(pages_text)

        details = {
            "Conclusion (Program 12)": conclusion
        }

        logger.info(f"Extracted case details from {pdf_path}: {details}")
        return details
    except Exception as e:
        logger.error(f"Error in Program 12 for {pdf_path}: {e}")
        return {"Error (Program 12)": str(e)}

# Export to Excel (append mode)
def export_to_excel(data: dict, output_path: str):
    try:
        # Convert dictionary to DataFrame
        df = pd.DataFrame([data])
        
        # Check if Excel file exists
        if os.path.exists(output_path):
            # Read existing Excel file
            existing_df = pd.read_excel(output_path)
            # Append new data
            df = pd.concat([existing_df, df], ignore_index=True)
        # Write to Excel
        df.to_excel(output_path, index=False)
        logger.info(f"Data appended to {output_path}")
    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")