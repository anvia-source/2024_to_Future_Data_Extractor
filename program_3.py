import pdfplumber
import re
import spacy
import langdetect
import logging
import pandas as pd
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("spaCy model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load spaCy model: {e}")
    exit(1)

# Extract text from PDF
def extract_text_from_pdf(pdf_file: str) -> str:
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

# Split text into paragraphs
def split_into_paragraphs(text: str) -> list:
    if not text or text.strip() == "":
        return []
    
    paragraphs = re.split(
        r'(?:\n\s*(\d+\.\s+))|(?:\n{2,})|(?=(?:Headnotes|Judgment|Order|List of Citations|Appearances|Conclusion|Discussion|Issue for Consideration|Question for Consideration)\b)',
        text
    )
    return [p.strip() for p in paragraphs if p and p.strip()]

# Check if a paragraph is a reference
def is_reference_paragraph(paragraph: str) -> bool:
    reference_indicators = [
        r"\bAIR\s+\d{4}\b",
        r"\bSCC\s+\d+\b",
        r"\b\d{4}\s+SCR\s+\d+\b",
        r"\[\d{4}\]\s+\d+\s+SC\s+\d+\b",
        r"\bvs?\.\s+[A-Za-z\s]+,\s*\d{4}\b",
        r"\bquoted\s+in\b",
        r"\brelied\s+upon\b",
        r"\bcase\s+of\s+[A-Za-z\s]+\s+v\s+",
        r"\breferred\s+to\s+in\b"
    ]
    for pattern in reference_indicators:
        if re.search(pattern, paragraph, re.IGNORECASE):
            return True
    return False

# Extract sections (laws, articles, rules, etc.)
def extract_sections(text: str) -> str:
    section_patterns = [
        r"(Section\s+\d+[A-Za-z]?(?:\(\d+\))?\s*(?:of\s+)?(?:the\s+)?([A-Za-z\s]+(?:Act|Code|Rules|Regulation|Ordinance)(?:,\s*\d{4})?))",
        r"(Article\s+\d+[A-Za-z]?(?:\(\d+\))?\s*(?:of\s+)?(?:the\s+)?([A-Za-z\s]+(?:Constitution)(?:,\s*\d{4})?))",
        r"(Rule\s+\d+[A-Za-z]?(?:\(\d+\))?\s*(?:of\s+)?(?:the\s+)?([A-Za-z\s]+(?:Rules|Regulations)(?:,\s*\d{4})?))",
        r"\b(Sec\.\s+\d+[A-Za-z]?(?:\(\d+\))?)\b",
        r"\b(Art\.\s+\d+[A-Za-z]?(?:\(\d+\))?)\b",
        r"(Section\s+\d+[A-Za-z]?/[A-Za-z\s]+(?:Act|Code|Rules|Regulation|Ordinance)(?:,\s*\d{4})?)",
        r"(Clause\s+\d+[A-Za-z]?\s*(?:of\s+)?(?:the\s+)?([A-Za-z\s]+(?:Act|Code|Rules|Constitution)(?:,\s*\d{4})?))"
    ]
    
    sections = []
    for pattern in section_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            sections.append(match.group(0).strip())
    
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "LAW" and ent.text not in sections:
            sections.append(ent.text)
    
    for para in split_into_paragraphs(text):
        if is_reference_paragraph(para):
            continue
        for pattern in section_patterns:
            matches = re.finditer(pattern, para, re.IGNORECASE)
            for match in matches:
                if match.group(0) not in sections:
                    sections.append(match.group(0).strip())
    
    return ", ".join(sections) if sections else "Not Found"

# Detect document language
def detect_language(text: str) -> str:
    try:
        lang = langdetect.detect(text[:1000])
        if lang == "en":
            return "English"
        elif lang == "hi":
            return "Hindi"
        elif lang == "ta":
            return "Tamil"
        else:
            return lang.capitalize()
    except:
        return "English"

# Main extraction function
def extract_judges(pdf_path: str) -> dict:
    try:
        text = extract_text_from_pdf(pdf_path)
        if not text:
            return {"Error (Program 3)": "No text extracted from PDF"}
        
        paragraphs = split_into_paragraphs(text)
        if not paragraphs:
            return {"Error (Program 3)": "No paragraphs extracted from PDF"}
        
        details = {
            "Section (Law Mentioned) (Program 3)": extract_sections(text),
            "Language of the Document (Program 3)": detect_language(text),
            "Country (Program 3)": "India"
        }
        
        return details
    except Exception as e:
        logger.error(f"Error in Program 3 for {pdf_path}: {str(e)}")
        return {"Error (Program 3)": str(e)}

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