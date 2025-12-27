import logging
import pdfplumber
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_file_path):
    try:
        text = ""
        with pdfplumber.open(pdf_file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_file_path}: {str(e)}")
        return ""

def extract_crime_info(pdf_path):
    try:
        text = extract_text_from_pdf(pdf_path)
        if not text:
            return {"Error (Program 10)": "No text extracted from PDF"}
        
        results = {
            "Crime against children (Program 10)": False,
            "Crime against women (Program 10)": False
        }
        
        patterns = {
            "Crime against children": [
                r"\bCrime\s+against\s+children\b",
                r"\bChild\s+sexual\s+abuse\b",
                r"\bChild\s+rape\b",
                r"\bSexual\s+assault\s+of\s+minor\b",
                r"\bChild\s+pornography\b|\bChild\s+sexual\s+exploitation\s+and\s*abuse\s+material\s*\(CSEAM\)\b|\bCSEAM\b",
                r"\bKidnapping\s+of\s+minor\b|\bChild\s+trafficking\b",
                r"\bChild\s+exploitation\b|\bMinor\s+victim\b",
                r"\bStorage\s*(?:\/|\s*or\s*)\s*possession\s+of\s+CSEAM\b|\bConstructive\s+possession\b|\bCyber\s+Tipline\b|\bNCRB\s+report\b"
            ],
            "Crime against women": [
                r"\bCrime\s+against\s+women\b",
                r"\bRape\b(?!\s+of\s+child)",
                r"\bGang\s+rape\b",
                r"\bMarital\s+rape\b",
                r"\bSexual\s+assault\b(?!\s+of\s+minor)",
                r"\bMolestation\b",
                r"\bOutraging\s+modesty\s+of\s+a\s+woman\b",
                r"\bSexual\s+harassment\b",
                r"\bDomestic\s+violence\b",
                r"\bDowry\s+harassment\b",
                r"\bDowry\s+death\b",
                r"\bCruelty\s+by\s+husband\s+or\s+relatives\b",
                r"\bAssault\s+on\s+women\b",
                r"\bAcid\s+attack\b"
            ]
        }
        
        legal_jargon = [
            r"\babuse\s+of\s+process\b",
            r"\babused\s+the\s+process\b",
            r"\babuse\s+of\s+law\b",
            r"\bharassment\s+to\s+the\s+other\s+party\b",
            r"\bmens\s+rea\s+in\s+general\s+law\b"
        ]
        
        citation_patterns = [
            r"\w+\s+v\.\s+\w+.*?\d{4}\s*(?:SCR|SCC|AIR|INSC)\b",
            r"\[\d{4}\]\s*\d+\s*(?:SCR|SCC)\b",
            r"(?:[A-Z][a-z]+\s+){2,}.*?\(\d{4}\)",
            r"\breferred\s+to\b|\brelied\s+on\b|\bheld\s+inapplicable\b",
            r"\bCrime\s+against\s+wom[ae]n\s+and\s+children\s*Branch\b"
        ]
        
        female_victim_context = r"\b(?:woman|women|female|girl|lady|victim\s*(?:was|is)\s*(?:a\s*)?(?:woman|female|girl|adult\s*female)|wife|mother|sister|daughter)\b"
        child_context = r"\b(?:child|children|minor|boy|girl\s*(?:under|aged\s*\d+\s*years))\b"
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for sentence in sentences:
            if any(re.search(citation, sentence, re.IGNORECASE) for citation in citation_patterns):
                continue
            
            if any(re.search(jargon, sentence, re.IGNORECASE) for jargon in legal_jargon):
                continue
            
            for category, regex_list in patterns.items():
                for pattern in regex_list:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        if category == "Crime against women":
                            if pattern == r"\bCrime\s+against\s+women\b":
                                results["Crime against women (Program 10)"] = True
                                continue
                            if not re.search(female_victim_context, sentence, re.IGNORECASE):
                                continue
                        elif category == "Crime against children":
                            if pattern == r"\bCrime\s+against\s+children\b":
                                results["Crime against children (Program 10)"] = True
                                continue
                            if not re.search(child_context, sentence, re.IGNORECASE):
                                continue
                        
                        results[category + " (Program 10)"] = True
        
        return results
    except Exception as e:
        logger.error(f"Error in Program 10 for {pdf_path}: {str(e)}")
        return {"Error (Program 10)": str(e)}