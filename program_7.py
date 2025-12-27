import pdfplumber
import re
import pytesseract
import logging
from PIL import Image
import io
from pdf2image import convert_from_bytes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_jumbled_citation(text, original_line=None):
    corrections = {'O': '0', 'I': '1', 'T': '7'}
    cleaned_text = text
    for wrong, right in corrections.items():
        cleaned_text = cleaned_text.replace(wrong, right)
    
    correct_format = re.match(r"\[\d{4}\]\s*\d+\s*(?:S\.C\.R\.|SCC|AIR|INSC)\s*\d+$", cleaned_text)
    if correct_format:
        return cleaned_text
    
    if original_line:
        original_cleaned = original_line
        for wrong, right in corrections.items():
            original_cleaned = original_cleaned.replace(wrong, right)
        
        partial_match = re.match(r"\[\d{4}\]\s*\d+\s*(S\.C\.R\.|SCC|AIR|INSC)$", cleaned_text)
        if partial_match:
            page_match = re.search(r"^\d+", original_cleaned)
            if page_match:
                page = page_match.group(0)
                return f"{cleaned_text} {page}"
        
        correct_match = re.search(r"\[(\d{4})\]\s*(\d+)\s*(S\.C\.R\.|SCC|AIR|INSC)", original_cleaned)
        page_match = re.search(r"^\d+", original_cleaned)
        
        if correct_match and page_match:
            year = correct_match.group(1)
            volume = correct_match.group(2)
            reporter = correct_match.group(3)
            page = page_match.group(0)
            return f"[{year}] {volume} {reporter} {page}"
    
    year_match = re.search(r"\[\d{4}\]", cleaned_text)
    volume_match = re.search(r"\b(\d+)\b", cleaned_text)
    reporter_match = re.search(r"(S\.C\.R\.|SCC|AIR|INSC)", cleaned_text, re.IGNORECASE)
    page_match = re.search(r"\b(\d+)$", cleaned_text)
    
    year = year_match.group(0)[1:-1] if year_match else "Unknown"
    volume = volume_match.group(1) if volume_match else ""
    reporter = reporter_match.group(1) if reporter_match else "S.C.R."
    page = page_match.group(1) if page_match else ""
    
    if year != "Unknown" and volume and reporter and page:
        return f"[{year}] {volume} {reporter} {page}"
    return text

def extract_citation(pdf_path):
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            first_page = pdf.pages[0]
            text = first_page.extract_text()
        
        if not text:
            with open(pdf_path, 'rb') as f:
                images = convert_from_bytes(f.read(), first_page=1, last_page=1, dpi=300)
                if images:
                    text = pytesseract.image_to_string(images[0], lang='eng', config='--psm 6')
        
        if text:
            pattern = r"\[\d{4}\]\s*\d+\s*(?:S\.C\.R\.|SCC|AIR|INSC)(?:\s*\d+)?|(?:[\[\(\{]?\d{4}[\]\)\}]?)\s*(?:\d+\s+)?(?:[A-Z\.]+)?\s*\d+(?:\s*[:–\-\s]\s*(?:[\[\(\{]?\d{4}[\]\)\}]?|\d+)\s*(?:[A-Z\.]+)?\s*\d+)?(?:\s*[:–\-]\s*\d+)?(?:\s*[A-Z]+\s*\d+)?(?:\s*[:–\-]\s*[A-Z]+\s*\d+)?"
            
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            citation = None
            
            if lines:
                match = re.search(pattern, lines[0])
                if match:
                    citation = match.group(0)
            
            if citation:
                citation = clean_jumbled_citation(citation, original_line=lines[0] if lines else None)
            else:
                citation = "\n".join(lines[:2]) if lines else ""
                citation = clean_jumbled_citation(citation, original_line=lines[0] if lines else None)
            
            return {"Citation (Program 7)": citation if citation else "Not Found"}
        return {"Error (Program 7)": "No text extracted from first page"}
    except Exception as e:
        logger.error(f"Error in Program 7 for {pdf_path}: {str(e)}")
        return {"Error (Program 7)": str(e)}