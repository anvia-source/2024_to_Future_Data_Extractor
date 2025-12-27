import pdfplumber
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_file):
    try:
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_file}: {str(e)}")
        return ""

def extract_acts(pdf_path):
    try:
        text = extract_text_from_pdf(pdf_path)
        if not text:
            return {"Error (Program 6)": "No text extracted from PDF"}
        
        list_of_acts_pattern = r"(List of Acts[\s\S]*?)(?=\n(?:List of Keywords|Case Arising From|$))"
        match = re.search(list_of_acts_pattern, text, re.IGNORECASE)
        
        if not match:
            return {"List of Acts (Program 6)": "Not Found"}
        
        raw_list_of_acts = match.group(1).strip()
        return {"List of Acts (Program 6)": raw_list_of_acts}
    except Exception as e:
        logger.error(f"Error in Program 6 for {pdf_path}: {str(e)}")
        return {"Error (Program 6)": str(e)}