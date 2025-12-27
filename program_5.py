import pdfplumber
import re
import logging
import pandas as pd
import os
from typing import List, Tuple

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

def split_into_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs based on common delimiters."""
    paragraphs = re.split(r'\n\s*\n|\n\s*\d+\.\s+', text)
    return [p.strip() for p in paragraphs if p.strip()]

def find_citations_in_paragraphs(paragraphs: List[str]) -> List[Tuple[str, str]]:
    """Find paragraphs containing case citations."""
    case_pattern = re.compile(
        r'(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:vs?\.?|versus|v\/s)\s+(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+&?\s*(?:Ors\.?|Others))?(?:\s*,\s*[0-9]{4})?(?:\s*\[[0-9]{4}\])?(?:\s+[A-Z]+\s+[A-Za-z]+)?)',
        re.IGNORECASE
    )
        
    citations = []
    for para in paragraphs:
        matches = case_pattern.findall(para)
        if matches:
            case_names = list(set(matches))
            citations.append((case_names, para))
        
    return citations

# Extract citations from the PDF
def extract_citations(pdf_path: str) -> dict:
    try:
        text = extract_text_from_pdf(pdf_path)
        if not text:
            return {"Error (Program 5)": "No text extracted from PDF"}

        details = {
            "Citations Found (Program 5)": "Not found",
            "Citation Details (Program 5)": "Not found"
        }

        paragraphs = split_into_paragraphs(text)
        citations = find_citations_in_paragraphs(paragraphs)
        
        if citations:
            # Extract case names from all citations
            all_case_names = []
            citation_details = []
            
            for i, (case_names, paragraph) in enumerate(citations, 1):
                all_case_names.extend(case_names)
                # Store first 200 characters of each paragraph for details
                para_preview = paragraph[:200] + "..." if len(paragraph) > 200 else paragraph
                citation_details.append(f"Citation {i}: {', '.join(case_names)} | Context: {para_preview}")
            
            # Remove duplicates and join
            unique_case_names = list(set(all_case_names))
            details["Citations Found (Program 5)"] = "; ".join(unique_case_names)
            details["Citation Details (Program 5)"] = " || ".join(citation_details)
        else:
            details["Citations Found (Program 5)"] = "No citations found"
            details["Citation Details (Program 5)"] = "No citation details available"

        logger.info(f"Extracted {len(citations)} citations from {pdf_path}")
        return details
    except Exception as e:
        logger.error(f"Error in Program 5 for {pdf_path}: {e}")
        return {"Error (Program 5)": str(e)}

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