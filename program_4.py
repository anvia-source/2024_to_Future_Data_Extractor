import PyPDF2
import re
import logging
import sys
import pandas as pd
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                extracted = page.extract_text() or ""
                text += extracted + " "
            if not text.strip():
                logger.warning("No text extracted from PDF.")
                return ""
            logger.info(f"Extracted {len(text)} characters from PDF.")
            return text
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        return ""

# Function to extract and categorize unique Acts, Rules, Laws, Procedures, Penal Codes, and Constitutions
def extract_legal_references(pdf_path: str) -> dict:
    try:
        text = extract_text_from_pdf(pdf_path)
        if not text:
            return {"Error (Program 4)": "No text extracted from PDF"}
        
        # Preprocess text to handle line breaks
        text = re.sub(r'\n\s*', ' ', text)

        # Regex patterns for each category
        act_pattern = r'(?:(?:A of\s+|like those contained in\s+|of\s+|s\s+)?)([A-Z][a-zA-Z\s]*(?:\s*\([A-Za-z\s,]+\))*\s*(?:[Aa][Cc][Tt]|[Aa][Cc][Tt][Ss])(?:,\s+\d{4}|\s+\d{4}|,\s*\d{4}(?:\s*\([A-Za-z\s]+\))?))'
        rule_pattern = r'(?:(?:A of\s+|like those contained in\s+|of\s+|s\s+)?)([A-Z][a-zA-Z\s]*(?:\s*\([A-Za-z\s,]+\))*\s*(?:[Rr][Uu][Ll][Ee]|[Rr][Uu][Ll][Ee][Ss])(?:,\s+\d{4}|\s+\d{4}|,\s*\d{4}(?:\s*\([A-Za-z\s]+\))?))'
        law_pattern = r'(?:(?:A of\s+|like those contained in\s+|of\s+|s\s+)?)((?:[A-Z][a-zA-Z]+)\s*(?:[Ll][Aa][Ww]|[Ll][Aa][Ww][Ss])(?:,\s+\d{4}|\s+\d{4}|,\s*\d{4}(?:\s*\([A-Za-z\s]+\))?)?)'
        procedure_pattern = r'(?:(?:A of\s+|like those contained in\s+|of\s+|s\s+)?)((?:Code of Criminal Procedure|CrPC|Code of Civil Procedure|CPC),\s+\d{4})'
        penal_code_pattern = r'(?:(?:A of\s+|like those contained in\s+|of\s+|s\s+)?)((?:Penal Code|Indian Penal Code|IPC),\s+\d{4})'
        constitution_pattern = r'(?:(?:A of\s+|like those contained in\s+|of\s+|s\s+)?)((?:Constitution of India|Constitutional)\s*-\s*Article\s*\d+[A-Za-z]?(?:\s*\([A-Za-z\s]+\))?)'

        # Extract matches
        acts_found = re.findall(act_pattern, text, re.IGNORECASE)
        rules_found = re.findall(rule_pattern, text, re.IGNORECASE)
        laws_found = re.findall(law_pattern, text, re.IGNORECASE)
        procedures_found = re.findall(procedure_pattern, text, re.IGNORECASE)
        penal_codes_found = re.findall(penal_code_pattern, text, re.IGNORECASE)
        constitutions_found = re.findall(constitution_pattern, text, re.IGNORECASE)

        # Remove duplicates and sort
        unique_acts = sorted(list(set(acts_found)))
        unique_rules = sorted(list(set(rules_found)))
        unique_procedures = sorted(list(set(procedures_found)))
        unique_penal_codes = sorted(list(set(penal_codes_found)))
        unique_constitutions = sorted(list(set(constitutions_found)))

        # Conditional law extraction: only if fewer than 5 details in other categories
        total_other_details = len(unique_acts) + len(unique_rules) + len(unique_procedures) + len(unique_penal_codes) + len(unique_constitutions)
        if total_other_details >= 5:
            unique_laws = ["Not found"]
        else:
            # Filter out unwanted laws
            unwanted_laws = {'law', 'that law', 'as law', 'a law', 'new law', 'case law', 'no law', 'other law'}
            unique_laws = sorted(list(set(law for law in laws_found if law.lower() not in unwanted_laws)))
            unique_laws = unique_laws if unique_laws else ["Not found"]

        # Prepare output dictionary
        details = {
            "Acts (Program 4)": ", ".join(unique_acts) if unique_acts else "Not found",
            "Rules (Program 4)": ", ".join(unique_rules) if unique_rules else "Not found",
            "Laws (Program 4)": ", ".join(unique_laws) if unique_laws else "Not found",
            "Procedures (Program 4)": ", ".join(unique_procedures) if unique_procedures else "Not found",
            "Penal Codes (Program 4)": ", ".join(unique_penal_codes) if unique_penal_codes else "Not found",
            "Constitutions (Program 4)": ", ".join(unique_constitutions) if unique_constitutions else "Not found"
        }

        # Log extracted references
        logger.info(f"Extracted legal references from {pdf_path}: {details}")
        return details
    except Exception as e:
        logger.error(f"Error in Program 4 for {pdf_path}: {e}")
        return {"Error (Program 4)": str(e)}

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