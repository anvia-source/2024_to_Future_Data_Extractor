import pdfplumber
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Extract text from the PDF
def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text:
                    text += page_text + "\n"
        if not text.strip():
            logger.warning(f"No text extracted from PDF {pdf_path}.")
            return ""
        logger.info(f"Extracted {len(text)} characters from PDF {pdf_path}.")
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
        return ""

# Extract the raw content of specified sections
def extract_background(pdf_path: str) -> dict:
    try:
        text = extract_text_from_pdf(pdf_path)
        if not text:
            return {"Error (Program 8)": "No text extracted from PDF"}

        details = {
            "Case Arising From (Program 8)": "Not found"
        }

        section_boundary = r"(?=\n{1,2}(?:[A-Z\s]{10,}(?:\n|$)|[0-9]{1,4}$|[A-Z]$|Judgment / Order of the Supreme Court|List of Acts|$))"

        case_keywords = [
            "From the Judgment and Order(?:s)?",
            "Judgment and Order dated",
            "Judgment dated",
            "Order of the Court",
            "Arising From"
        ]

        # Extract Case Arising From
        case_arising_pattern = r"(?:(?:[A-Z\s:]+JURISDICTION.*?\n)?(?:.*?\n)?)(Case Arising From[\s\S]*?)" + section_boundary
        match = re.search(case_arising_pattern, text, re.IGNORECASE)
        if match:
            details["Case Arising From (Program 8)"] = match.group(0).strip()
        else:
            fallback_pattern = r"(?:(?:[A-Z\s:]+JURISDICTION.*?\n)?(?:.*?\n)?)((?:" + "|".join(case_keywords) + r")[\s\S]*?)" + section_boundary
            matches = list(re.finditer(fallback_pattern, text, re.IGNORECASE))
            if matches:
                best_match = None
                for match in matches:
                    full_text = match.group(0).strip()
                    if "JURISDICTION" in full_text.upper():
                        best_match = match
                        break
                if not best_match:
                    best_match = matches[0]
                details["Case Arising From (Program 8)"] = best_match.group(0).strip()

        logger.info(f"Extracted background details from {pdf_path}: {details}")
        return details
    except Exception as e:
        logger.error(f"Error in Program 8 for {pdf_path}: {e}")
        return {"Error (Program 8)": str(e)}