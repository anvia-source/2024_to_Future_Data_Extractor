import pdfplumber
import re
import spacy
import logging
import sys
import pandas as pd
from typing import Optional, Tuple
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
    sys.exit(1)

# Case type mappings
CASE_CATEGORIES = {
    "Civil": [
        "Advisory Jurisdiction", "Arbitration Petition", "Civil Appeal", "Civil Miscellaneous Petition",
        "Original Suit", "Review Petition (Civil)", "Special Leave Petition (Civil)",
        "Suo Motu Writ Petition (Civil)", "Suo Motu Contempt Petition (Civil)",
        "Suo Motu Transfer Petition (Civil)", "Transfer Petition (Civil)", "Transferred Case (Civil)",
        "Writ Petition (Civil)", "Contempt Petition (Civil)", "Curative Petition (Civil)",
        "Election Petition (Civil)"
    ],
    "Criminal": [
        "Review Petition (Criminal)", "Special Leave Petition (Criminal)", "Suo Motu Writ (Criminal)",
        "Suo Motu Contempt Petition (Criminal)", "Suo Motu Transfer Petition (Criminal)",
        "Suo Motu Writ Petition (Criminal)", "Transfer Petition (Criminal)", "Transferred Case (Criminal)",
        "Writ Petition (Criminal)", "Contempt Petition (Criminal)", "Criminal Appeal",
        "Criminal Miscellaneous Petition", "Curative Petition (Criminal)", "Death Reference Case",
        "Motion (CRL)"
    ],
    "Others": [
        "Ref. U/A 317(1)", "Ref. U/S 14 RTI", "Ref. U/S 143", "Ref. U/S 17 RTI", "Special Reference Case",
        "Tax Reference Case", "Disciplinary Jurisdiction", "Excise Reference No", "Habeas Corpus Petition",
        "Miscellaneous Application", "All Sea"
    ]
}

# Short form to full form mapping (case-insensitive)
SUBCATEGORY_SHORT_FORMS = {
    "writ petition (c)": "Writ Petition (Civil)",
    "smw (civil)": "Suo Motu Writ Petition (Civil)",
    "smw (crl)": "Suo Motu Writ (Criminal)",
    "writ petition (crl)": "Writ Petition (Criminal)",
    "slp (civil)": "Special Leave Petition (Civil)",
    "slp (crl)": "Special Leave Petition (Criminal)",
    "suo motu writ (civil)": "Suo Motu Writ Petition (Civil)",
    "suo motu writ (crl)": "Suo Motu Writ (Criminal)",
    "motion (crl)": "Motion (CRL)",
    "ref. u/a 317(1)": "Ref. U/A 317(1)",
    "ref. u/s 14 rti": "Ref. U/S 14 RTI",
    "ref. u/s 143": "Ref. U/S 143",
    "ref. u/s 17 rti": "Ref. U/S 17 RTI"
}

# Normalize subcategory to full form
def normalize_subcategory(subcat: str) -> str:
    subcat_lower = subcat.lower().strip()
    for short_form, full_form in SUBCATEGORY_SHORT_FORMS.items():
        if re.fullmatch(re.escape(short_form), subcat_lower, re.IGNORECASE):
            return full_form
    return subcat

# Extract text from PDF
def extract_text_from_pdf(pdf_file: str) -> str:
    try:
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
        if not text.strip():
            logger.warning("No text extracted from PDF.")
            return ""
        logger.info(f"Extracted {len(text)} characters from PDF.")
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return ""

# Split text into paragraphs
def split_into_paragraphs(text: str) -> list:
    if not text or text.strip() == "":
        return []
    paragraphs = re.split(
        r'(?:\n\s*(\d+\.\s+))|(?:\n{2,})|(?=(?:Headnotes|Judgment|Order|List of Citations|Appearances|Conclusion|Discussion|Issue for Consideration|Question for Consideration)\b)',
        text
    )
    result = [para.strip() for para in paragraphs if para and para.strip()]
    return result

# Extract Case Title, Citation, and Potential Subcategory
def extract_case_title(text: str, first_paragraph: str) -> Tuple[str, str, Optional[str]]:
    # Clean text to remove non-printable and non-ASCII characters
    cleaned_text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)
    first_page_lines = cleaned_text.splitlines()[:10]  # Check up to 10 lines
    # Print first 7 lines to terminal
    print(f"\nFirst 7 lines of extracted text:")
    for i, line in enumerate(first_page_lines[:7], 1):
        print(f"Line {i}: {line}")
    
    # Log first 7 lines for debugging
    logger.debug(f"Raw first 7 lines: {first_page_lines[:7]}")
    
    # Look for citation in the first line
    citation = "Not found"
    title = "Not found"
    subcategory = None
    citation_pattern = r'\[\d{4}\]\s+\d+\s+S\.C\.R\.\s+\d+\s*:\s*\d+\s+INSC\s+\d+'
    all_subcats = list(CASE_CATEGORIES["Civil"]) + list(CASE_CATEGORIES["Criminal"]) + list(CASE_CATEGORIES["Others"])
    all_subcats.extend(SUBCATEGORY_SHORT_FORMS.keys())
    # Pattern for subcategories (standalone or in parentheses)
    subcategory_pattern = r'\b(' + '|'.join(re.escape(subcat) for subcat in all_subcats) + r'|special\s*reference|reference\s*case|reference)\b\s*(?:no\.?\s*[0-9/]+\s*(?:of\s*\d{4})?)?'
    paren_subcat_pattern = r'\(\s*(' + '|'.join(re.escape(subcat) for subcat in all_subcats) + r'|special\s*reference|reference\s*case|reference)\s*(?:no\.?\s*[0-9/]+\s*(?:of\s*\d{4})?)?\s*\)'
    
    try:
        first_line = first_page_lines[0].strip() if first_page_lines else ""
        citation_match = re.search(citation_pattern, first_line, re.IGNORECASE)
        if citation_match:
            citation = citation_match.group(0).strip()
            logger.debug(f"Found citation: '{citation}'")
        
        # Check first page text for single-line title
        first_page_text = '\n'.join(first_page_lines)
        title_pattern = r'([^\n]+?)\s+v(?:s|ersus)?\.?\s+([^\n\(]+)(?:\s*\((' + '|'.join(re.escape(subcat) for subcat in all_subcats) + r')\b\s*(?:no\.?\s*[0-9/]+\s*(?:of\s*\d{4})?)?\))?'
        match = re.search(title_pattern, first_page_text, re.IGNORECASE)
        if match:
            filer = match.group(1).strip()
            against = re.sub(r'\s*etc\.?$', '', match.group(2).strip(), flags=re.IGNORECASE)
            title = f"{filer} v. {against}"
            title = re.sub(r'\s+', ' ', title).strip()
            title = re.sub(r'\s*\(.*?\)$', '', title).strip()
            if match.group(3):
                subcategory = normalize_subcategory(match.group(3).strip())
                if subcategory in ["Special Reference", "Reference Case", "Reference"]:
                    subcategory = "Special Reference Case"
                logger.debug(f"Found subcategory in title: '{subcategory}'")
            logger.info(f"Extracted case title (single-line): Citation='{citation}', Title='{title}', Subcategory='{subcategory}'")
            return citation, title, subcategory
        
        # Line-by-line approach for split titles
        next_lines = first_page_lines[1:8] if len(first_page_lines) > 1 else []
        logger.debug(f"Next lines for title: {next_lines}")
        for i, line in enumerate(next_lines):
            line = line.strip()
            versus_match = re.search(r'^\s*v(?:s|ersus)?\.?\s+(.+)', line, re.IGNORECASE)
            if versus_match and i > 0:
                first_party = next_lines[i-1].strip() if i-1 >= 0 else ""
                second_party = re.sub(r'\s*etc\.?$', '', versus_match.group(1).strip(), flags=re.IGNORECASE)
                # Check if second_party includes subcategory
                subcat_match = re.search(r'(.+?)\s*\((' + '|'.join(re.escape(subcat) for subcat in all_subcats) + r')\b\s*(?:no\.?\s*[0-9/]+\s*(?:of\s*\d{4})?)?\)', second_party, re.IGNORECASE)
                if subcat_match:
                    second_party = subcat_match.group(1).strip()
                    subcategory = normalize_subcategory(subcat_match.group(2).strip())
                    if subcategory in ["Special Reference", "Reference Case", "Reference"]:
                        subcategory = "Special Reference Case"
                    logger.debug(f"Found subcategory in second party: '{subcategory}'")
                if first_party and second_party:
                    title = f"{first_party} v. {second_party}"
                    title = re.sub(r'\s+', ' ', title).strip()
                    title = re.sub(r'\s*\(.*?\)$', '', title).strip()
                    logger.info(f"Extracted case title (line-by-line): Citation='{citation}', Title='{title}', Subcategory='{subcategory}'")
                    return citation, title, subcategory
        
        # Check for "In Re" cases
        combined_lines = ' '.join(line.strip() for line in next_lines if line.strip())
        combined_lines = re.sub(r'\s+', ' ', combined_lines).strip()
        in_re_pattern = r'(In\s+Re[\s:]+)(.+?)(?=\s*(?:etc\.|\(|$))'
        in_re_match = re.search(in_re_pattern, combined_lines, re.IGNORECASE)
        if in_re_match:
            title = f"In Re: {in_re_match.group(2).strip()}"
            title = re.sub(r'\s*etc\.?$', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s+', ' ', title).strip()
            # Check same line and next lines for subcategory
            title_line_index = next(i for i, line in enumerate(first_page_lines) if re.search(in_re_pattern, line, re.IGNORECASE))
            title_line = first_page_lines[title_line_index].strip()
            subcat_match = re.search(paren_subcat_pattern, title_line, re.IGNORECASE)
            if subcat_match:
                subcategory = normalize_subcategory(subcat_match.group(1).strip())
                if subcategory in ["Special Reference", "Reference Case", "Reference"]:
                    subcategory = "Special Reference Case"
                logger.debug(f"Found subcategory in In Re title line: '{subcategory}'")
            else:
                # Check subsequent lines (up to 7)
                for line in first_page_lines[title_line_index + 1:8]:
                    # Try both patterns for flexibility
                    subcat_match = re.search(paren_subcat_pattern, line, re.IGNORECASE)
                    if subcat_match:
                        subcategory = normalize_subcategory(subcat_match.group(1).strip())
                        if subcategory in ["Special Reference", "Reference Case", "Reference"]:
                            subcategory = "Special Reference Case"
                        logger.debug(f"Found subcategory after In Re on line {first_page_lines.index(line) + 1}: '{subcategory}'")
                        break
                    subcat_match = re.search(subcategory_pattern, line, re.IGNORECASE)
                    if subcat_match:
                        subcategory = normalize_subcategory(subcat_match.group(1).strip())
                        if subcategory in ["Special Reference", "Reference Case", "Reference"]:
                            subcategory = "Special Reference Case"
                        logger.debug(f"Found subcategory after In Re on line {first_page_lines.index(line) + 1}: '{subcategory}'")
                        break
            logger.info(f"Extracted In Re case title: Citation='{citation}', Title='{title}', Subcategory='{subcategory}'")
            return citation, title, subcategory
    except Exception as e:
        logger.error(f"Error in title parsing: {str(e)}")
    
    # Fallback: spaCy-based entity recognition
    try:
        doc = nlp(combined_lines if combined_lines else first_paragraph[:200])
        entities = [(ent.text, ent.label_) for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "GPE"]]
        if len(entities) >= 2:
            filer = entities[0][0].strip()
            against = re.sub(r'\s*etc\.?$', '', entities[1][0].strip(), flags=re.IGNORECASE)
            title = f"{filer} v. {against}"
            title = re.sub(r'\s*\(.*?\)$', '', title).strip()
            title = re.sub(r'\s+', ' ', title).strip()
            # Check next lines for subcategory
            for line in next_lines:
                subcat_match = re.search(paren_subcat_pattern, line, re.IGNORECASE)
                if subcat_match:
                    subcategory = normalize_subcategory(subcat_match.group(1).strip())
                    if subcategory in ["Special Reference", "Reference Case", "Reference"]:
                        subcategory = "Special Reference Case"
                    logger.debug(f"Found subcategory in fallback: '{subcategory}'")
                    break
                subcat_match = re.search(subcategory_pattern, line, re.IGNORECASE)
                if subcat_match:
                    subcategory = normalize_subcategory(subcat_match.group(1).strip())
                    if subcategory in ["Special Reference", "Reference Case", "Reference"]:
                        subcategory = "Special Reference Case"
                    logger.debug(f"Found subcategory in fallback: '{subcategory}'")
                    break
            logger.info(f"Extracted case title (spaCy-based): Citation='{citation}', Title='{title}', Subcategory='{subcategory}'")
            return citation, title, subcategory
    except Exception as e:
        logger.error(f"Error in spaCy-based title parsing: {str(e)}")
    
    # Fallback: Clean combined lines or first paragraph
    logger.debug("Falling back to combined lines or first paragraph")
    title = combined_lines if combined_lines else first_paragraph.strip()[:100]
    title = re.sub(r'\s*\(.*no\.?\s*\d+.*|\s*\d{1,2}\s+[A-Za-z]+\s+20\d{2}.*|[\[].*J[\].].*$|\s*etc\.?$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s+', ' ', title).strip()
    # Check next lines for subcategory
    for line in next_lines:
        subcat_match = re.search(paren_subcat_pattern, line, re.IGNORECASE)
        if subcat_match:
            subcategory = normalize_subcategory(subcat_match.group(1).strip())
            if subcategory in ["Special Reference", "Reference Case", "Reference"]:
                subcategory = "Special Reference Case"
            logger.debug(f"Found subcategory in final fallback: '{subcategory}'")
            break
        subcat_match = re.search(subcategory_pattern, line, re.IGNORECASE)
        if subcat_match:
            subcategory = normalize_subcategory(subcat_match.group(1).strip())
            if subcategory in ["Special Reference", "Reference Case", "Reference"]:
                subcategory = "Special Reference Case"
            logger.debug(f"Found subcategory in final fallback: '{subcategory}'")
            break
    logger.info(f"Extracted fallback title: Citation='{citation}', Title='{title}', Subcategory='{subcategory}'")
    return citation, title, subcategory

# Extract hearing dates and number of hearings
def extract_hearing_dates(text: str) -> Tuple[list, int]:
    date_pattern = r'\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{4}'
    hearing_dates = []
    hearing_context_pattern = r'(hearing|heard|reserved|arguments\s*advanced|court\s*convened)\s*(?:on|dated)?\s*(' + date_pattern + ')'
    try:
        matches = re.findall(hearing_context_pattern, text, re.IGNORECASE)
        hearing_dates.extend([match[1] for match in matches])
    except Exception as e:
        logger.error(f"Error in hearing dates regex: {str(e)}")
    
    if not hearing_dates:
        try:
            all_dates = re.findall(date_pattern, text, re.IGNORECASE)
            doc = nlp(text[:5000])
            for ent in doc.ents:
                if ent.label_ == "DATE" and ent.text in all_dates:
                    hearing_dates.append(ent.text)
        except Exception as e:
            logger.error(f"Error in spaCy date extraction: {str(e)}")
    
    hearing_dates = list(dict.fromkeys(hearing_dates))
    num_hearings = len(hearing_dates) if hearing_dates else 0
    return hearing_dates, num_hearings

# Determine Category and Subcategory
def determine_category_subcategory(text: str, case_title: str = "", extracted_subcategory: Optional[str] = None) -> Tuple[str, list]:
    category = "Unknown"
    subcategories = []
    
    # Use extracted subcategory if provided
    if extracted_subcategory:
        subcategory = normalize_subcategory(extracted_subcategory)
        if subcategory in ["Special Reference", "Reference Case", "Reference"]:
            subcategory = "Special Reference Case"
        subcategories.append(subcategory)
        for cat, subcats in CASE_CATEGORIES.items():
            if subcategory in subcats:
                category = cat
                logger.info(f"Using extracted subcategory: '{subcategory}', Category: '{category}'")
                break
        if category != "Unknown":
            return category, subcategories
    
    # Create a regex pattern for all subcategories
    all_subcats = list(CASE_CATEGORIES["Civil"]) + list(CASE_CATEGORIES["Criminal"]) + list(CASE_CATEGORIES["Others"])
    all_subcats.extend(SUBCATEGORY_SHORT_FORMS.keys())
    subcategory_pattern = r'\b(' + '|'.join(re.escape(subcat) for subcat in all_subcats) + r'|special\s*reference|reference\s*case|reference)\b\s*(?:no\.?\s*[0-9/]+\s*(?:of\s*\d{4})?)?'
    paren_subcat_pattern = r'\(\s*(' + '|'.join(re.escape(subcat) for subcat in all_subcats) + r'|special\s*reference|reference\s*case|reference)\s*(?:no\.?\s*[0-9/]+\s*(?:of\s*\d{4})?)?\s*\)'
    
    # Check lines 1-7 for subcategory
    lines = text.splitlines()
    target_lines = lines[:7] if len(lines) >= 7 else lines
    logger.debug(f"Target lines for subcategory: {target_lines}")
    
    for line in target_lines:
        try:
            match = re.search(paren_subcat_pattern, line, re.IGNORECASE)
            if match:
                subcat = normalize_subcategory(match.group(1).strip())
                if subcat in ["Special Reference", "Reference Case", "Reference"]:
                    subcat = "Special Reference Case"
                subcategories.append(subcat)
                for cat, subcats in CASE_CATEGORIES.items():
                    if subcat in subcats:
                        category = cat
                        break
                logger.info(f"Extracted subcategory from line {target_lines.index(line) + 1}: '{subcat}', Category: '{category}'")
                break
            match = re.search(subcategory_pattern, line, re.IGNORECASE)
            if match:
                subcat = normalize_subcategory(match.group(1).strip())
                if subcat in ["Special Reference", "Reference Case", "Reference"]:
                    subcat = "Special Reference Case"
                subcategories.append(subcat)
                for cat, subcats in CASE_CATEGORIES.items():
                    if subcat in subcats:
                        category = cat
                        break
                logger.info(f"Extracted subcategory from line {target_lines.index(line) + 1}: '{subcat}', Category: '{category}'")
                break
        except Exception as e:
            logger.error(f"Error in subcategory regex for line '{line}': {str(e)}")
    
    # Special handling for "In Re" cases
    if not subcategories and re.search(r'\s*In\s+Re[\s:]+', case_title, re.IGNORECASE):
        in_re_patterns = {
            "Writ Petition (Civil)": r'\b(?:writ\s*petition\s*\(c\)|writ\s*petition)\b',
            "Suo Motu Writ (Criminal)": r'\b(?:smw\s*\(crl\)|suo\s*motu\s*writ\s*\(criminal\))\b',
            "Suo Motu Writ Petition (Civil)": r'\b(?:smw\s*\(civil\)|suo\s*motu\s*writ\s*petition\s*\(civil\)|suo\s*motu\s*writ)\b',
            "Special Reference Case": r'\b(?:special\s*reference|reference\s*case|reference|constitutional)\b',
            "Habeas Corpus Petition": r'\bhabeas\s*corpus\b',
            "Miscellaneous Application": r'\bmiscellaneous\s*application\b'
        }
        for subcat, pattern in in_re_patterns.items():
            try:
                if re.search(pattern, case_title.lower() + ' ' + ' '.join(target_lines).lower(), re.IGNORECASE):
                    subcategories.append(subcat)
                    category = "Civil" if subcat in ["Writ Petition (Civil)", "Suo Motu Writ Petition (Civil)"] else "Criminal" if subcat == "Suo Motu Writ (Criminal)" else "Others"
                    logger.info(f"Extracted In Re subcategory: '{subcat}', Category: '{category}'")
                    break
            except Exception as e:
                logger.error(f"Error in In Re subcategory regex for {subcat}: {str(e)}")
    
    # Fallback to search first page (first 1000 characters)
    if not subcategories:
        first_page_text = text[:1000].lower()
        for cat, subcats in CASE_CATEGORIES.items():
            for subcat in subcats:
                pattern = r'\b' + re.escape(subcat.lower()) + r'\b'
                try:
                    if re.search(pattern, first_page_text, re.IGNORECASE):
                        subcategories.append(subcat)
                        if category == "Unknown":
                            category = cat
                        logger.info(f"Extracted subcategory from first page: '{subcat}', Category: '{category}'")
                except Exception as e:
                    logger.error(f"Error in subcategory fallback regex for {subcat}: {str(e)}")
    
    # Fallback for category if still unknown
    if category == "Unknown" and subcategories:
        for cat, subcats in CASE_CATEGORIES.items():
            if any(subcat in subcats for subcat in subcategories):
                category = cat
                break
    
    # If no subcategory found, set to Unknown
    if not subcategories:
        subcategories = ["Unknown"]
        logger.warning("No subcategory found, defaulting to 'Unknown'")
    
    return category, subcategories

# Clean party names
def clean_party_name(name: str) -> str:
    name = re.sub(r'\[\d{4}\].*?\d{4}\s*(?:SCC|INSC)\s*\d+', '', name)
    name = re.sub(r'Case\s+Details.*', '', name, flags=re.IGNORECASE)
    return name.strip(' -:\n.,;')

def remove_statute_names(name: str) -> str:
    statute_pattern = r'(?:the\s+)?(?:prevention\s+of|act|law|rules|regulation|code|section)\s+[a-zA-Z0-9\s]*(?=\b|$|[.,;])'
    name = re.sub(statute_pattern, '', name, flags=re.IGNORECASE)
    name = re.sub(r'(?:the\s+)?state\s+of\s*$', 'State of', name, flags=re.IGNORECASE)
    name = re.sub(r'(?:the\s+)?union\s+of\s*$', 'Union of', name, flags=re.IGNORECASE)
    return name.strip()

# Determine filer and against actions
def get_legal_actions(text: str) -> Tuple[str, str]:
    lower_text = text.lower()
    actions = {
        'civil appeal': ('Filed a Civil Appeal', 'Contested the Appeal'),
        'criminal appeal|appeal': ('Filed a Criminal Appeal', 'Contested the Appeal'),
        'writ petition': ('Filed a Writ Petition', 'Opposed the Writ Petition'),
        'special leave petition|slp': ('Filed a Special Leave Petition', 'Opposed the Special Leave Petition'),
        'revision petition': ('Filed a Revision Petition', 'Opposed the Revision Petition'),
        'suit': ('Filed a Suit', 'Defended the Suit'),
        'complaint': ('Filed a Complaint', 'Opposed the Complaint'),
        'bail application': ('Filed a Bail Application', 'Opposed the Bail Application'),
        'arbitration petition': ('Filed an Arbitration Petition', 'Opposed the Arbitration Petition')
    }
    for pattern, (filer, against) in actions.items():
        try:
            if re.search(pattern, lower_text, re.IGNORECASE):
                return filer, against
        except Exception as e:
            logger.error(f"Error in legal actions regex for {pattern}: {str(e)}")
    return 'Filed a Petition/Appeal', 'Opposed the Petition/Appeal'

# Extract party details
def extract_party_info(text: str, title: str) -> dict:
    details = {
        'Party Details (Program 2) - Filed By': 'Unknown',
        'Party Details (Program 2) - Against Who': 'Unknown',
        'Party Details (Program 2) - Filer Action': 'Unknown',
        'Party Details (Program 2) - Against Action': 'Unknown',
        'Party Details (Program 2) - Filer Name': 'Unknown',
        'Party Details (Program 2) - Against Name': 'Unknown',
        'Party Details (Program 2) - Filer Identity': 'Unknown',
        'Party Details (Program 2) - Filer Other Attributes': 'Unknown',
        'Party Details (Program 2) - Against Identity': 'Unknown',
        'Party Details (Program 2) - Against Other Attributes': 'Unknown'
    }
    debug_info = []
    org_indicators = ['ltd', 'limited', 'corporation', 'company', 'pvt', 'llp', 'inc', 'represented by']
    gov_indicators = ['state of', 'government', 'union of', 'ministry', 'department']
    ind_indicators = ['s/o', 'd/o', 'w/o', 'aged', 'years old']

    # Try extracting from title first
    title_patterns = [
        r'([^\n]+?)\s+v(?:s|ersus)?\.?\s+([^\n\(]+)(?:\s*\(.+\))?'
    ]
    filer_name = against_name = None
    for pattern in title_patterns:
        try:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                filer_name = clean_party_name(remove_statute_names(match.group(1)))
                against_name = clean_party_name(remove_statute_names(re.sub(r'\s*etc\.?$', '', match.group(2), flags=re.IGNORECASE)))
                debug_info.append(f"Extracted names via title regex: Filer='{filer_name}', Against='{against_name}'")
                break
        except Exception as e:
            logger.error(f"Error in title pattern regex: {str(e)}")
    
    # Fallback to text if title-based extraction fails
    if not filer_name or not against_name:
        keyword_patterns = {
            'filer': r'(petitioner|appellant|plaintiff)\s*[:;-]?\s*([^,\n;]+)',
            'against': r'(respondent|defendant)\s*[:;-]?\s*([^,\n;]+)'
        }
        for role, pattern in keyword_patterns.items():
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    name = clean_party_name(remove_statute_names(matches[0][1]))
                    if role == 'filer' and not filer_name:
                        filer_name = name
                        debug_info.append(f"Extracted filer name via keyword: '{name}'")
                    elif role == 'against' and not against_name:
                        against_name = name
                        debug_info.append(f"Extracted against name via keyword: '{name}'")
            except Exception as e:
                logger.error(f"Error in keyword pattern regex for {role}: {str(e)}")

    # Fallback to spaCy
    if not filer_name or not against_name:
        try:
            doc = nlp(text[:5000])
            entities = [(ent.text, ent.label_) for ent in doc.ents if ent.label_ in ['PERSON', 'ORG', 'GPE']]
            for i, (ent_text, ent_label) in enumerate(entities):
                name = clean_party_name(remove_statute_names(ent_text))
                if not filer_name and i == 0:
                    filer_name = name
                    debug_info.append(f"Extracted filer name via spaCy: '{name}' ({ent_label})")
                elif not against_name and i == 1:
                    against_name = name
                    debug_info.append(f"Extracted against name via spaCy: '{name}' ({ent_label})")
                    break
        except Exception as e:
            logger.error(f"Error in spaCy party extraction: {str(e)}")

    if filer_name and against_name:
        filer_action, against_action = get_legal_actions(text)
        details.update({
            'Party Details (Program 2) - Filer Name': filer_name,
            'Party Details (Program 2) - Against Name': against_name,
            'Party Details (Program 2) - Filed By': 'Petitioner/Appellant',
            'Party Details (Program 2) - Against Who': 'Respondent/Defendant',
            'Party Details (Program 2) - Filer Action': filer_action,
            'Party Details (Program 2) - Against Action': against_action
        })
        f_l, a_l = filer_name.lower(), against_name.lower()
        details['Party Details (Program 2) - Filer Identity'] = next((t for t, k in [('Individual', ind_indicators), ('Organization', org_indicators), ('Government', gov_indicators)] if any(k in f_l for k in k)), 'Other')
        details['Party Details (Program 2) - Against Identity'] = next((t for t, k in [('Individual', ind_indicators), ('Organization', org_indicators), ('Government', gov_indicators)] if any(k in a_l for k in k)), 'Other')
    
    logger.debug('Party extraction debug: ' + '; '.join(debug_info))
    return details

# Main extraction function
def extract_parties(pdf_path: str) -> dict:
    try:
        text = extract_text_from_pdf(pdf_path)
        if not text:
            return {'Error (Program 2)': 'No text extracted from PDF'}
        
        paragraphs = split_into_paragraphs(text)
        if not paragraphs:
            return {'Error (Program 2)': 'No paragraphs extracted from PDF'}
        
        first_paragraph = paragraphs[0]
        details = {
            'Citation (Program 2)': 'Unknown',
            'Case Title (Program 2)': 'Unknown',
            'Hearing Dates (Program 2)': 'Unknown',
            'Number of Hearings (Program 2)': 'Unknown',
            'Category (Program 2)': 'Unknown',
            'Subcategory (Program 2)': 'Unknown',
            'Party Details (Program 2) - Filed By': 'None',
            'Party Details (Program 2) - Against Who': 'None',
            'Party Details (Program 2) - Filer Action': 'None',
            'Party Details (Program 2) - Against Action': 'None',
            'Party Details (Program 2) - Filer Name': 'None',
            'Party Details (Program 2) - Against Name': 'None',
            'Party Details (Program 2) - Filer Identity': 'None',
            'Party Details (Program 2) - Filer Other Attributes': 'None',
            'Party Details (Program 2) - Against Identity': 'None',
            'Party Details (Program 2) - Against Other Attributes': 'None'
        }
        
        # Case Title, Citation, and Subcategory
        citation, case_title, extracted_subcategory = extract_case_title(text, first_paragraph)
        details['Citation (Program 2)'] = citation
        details['Case Title (Program 2)'] = case_title
        
        # Check for "In Re" cases
        in_re_match = re.search(r'\s*In\s+Re[\s:]+', case_title, re.IGNORECASE)
        is_in_re = bool(in_re_match)
        if is_in_re:
            logger.info(f"In Re case detected, setting party fields to None: '{case_title}'")
            # Set category and subcategory for In Re cases
            category, subcategories = determine_category_subcategory(text, case_title, extracted_subcategory)
            details['Category (Program 2)'] = category
            details['Subcategory (Program 2)'] = ', '.join(subcategories) if subcategories else 'Unknown'
        else:
            # Check for "v", "vs", or "versus"
            has_versus = re.search(r'\s+v(?:s|ersus)?\.?\s+', case_title, re.IGNORECASE)
            if has_versus:
                party_details = extract_party_info(text, case_title)
                details.update(party_details)
                logger.info(f"Versus found, party fields updated: '{case_title}'")
            else:
                # Try extracting parties from text even if versus not in title
                logger.info(f"No versus in title, attempting party extraction from text: '{case_title}'")
                party_details = extract_party_info(text, case_title)
                if party_details['Party Details (Program 2) - Filer Name'] != 'Unknown':
                    details.update(party_details)
                else:
                    logger.info(f"No valid parties extracted, keeping party fields as None: '{case_title}'")
            
            # Category and Subcategory
            category, subcategories = determine_category_subcategory(text, case_title, extracted_subcategory)
            details['Category (Program 2)'] = category
            details['Subcategory (Program 2)'] = ', '.join(subcategories) if subcategories else 'Unknown'
        
        # Hearing Dates and Number of Hearings
        hearing_dates, num_hearings = extract_hearing_dates(text)
        details['Hearing Dates (Program 2)'] = ', '.join(hearing_dates) if hearing_dates else 'Unknown'
        details['Number of Hearings (Program 2)'] = num_hearings if num_hearings > 0 else 'Unknown'
        
        return details
    except Exception as e:
        logger.error(f'Error in Program 2 for {pdf_path}: {str(e)}')
        return {'Error (Program 2)': str(e)}

# Export to Excel
def export_to_excel(data: dict, output_path: str):
    try:
        df = pd.DataFrame([data])
        if os.path.exists(output_path):
            existing_df = pd.read_excel(output_path)
            df = pd.concat([existing_df, df], ignore_index=True)
        df.to_excel(output_path, index=False)
        logger.info(f'Data appended to {output_path}')
    except Exception as e:
        logger.error(f'Error exporting to Excel: {str(e)}')