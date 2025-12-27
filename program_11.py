import logging
import pdfplumber
import re
import spacy

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    logger.error(f"Failed to load spaCy model 'en_core_web_sm': {str(e)}")
    nlp = None

# Extract text from PDF
def extract_text_from_pdf(pdf_file_path: str) -> str:
    try:
        text = ""
        with pdfplumber.open(pdf_file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
        if not text.strip():
            logger.warning(f"No text extracted from PDF {pdf_file_path}.")
            return ""
        logger.info(f"Extracted {len(text)} characters from PDF {pdf_file_path}.")
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_file_path}: {str(e)}")
        return ""

# Check if text is a reference/citation
def is_reference_text(text: str) -> bool:
    reference_indicators = [
        r"\bAIR\s+\d{4}\b",
        r"\bSCC\s+\d+\b",
        r"\b\d{4}\s+SCR\s+\d+\b",
        r"\[\d{4}\]\s+\d+\s+SC\s+\d+\b",
        r"\bvs?\.\s+[A-Za-z\s]+,\s*\d{4}\b",
        r"\bquoted\s+in\b",
        r"\brelied\s+upon\b",
        r"\bcase\s+of\s+[A-Za-z\s]+\s+v\s+",
        r"\breferred\s+to\s+in\b",
        r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*\[\d{4}\]"
    ]
    for pattern in reference_indicators:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

# Extract case result
def extract_case_result(pdf_path: str) -> dict:
    try:
        if not nlp:
            return {"case_result": "spaCy model 'en_core_web_sm' not loaded"}
        
        text = extract_text_from_pdf(pdf_path)
        if not text:
            return {"case_result": "No text extracted from PDF"}
        
        # Combined keyword patterns for singular and plural
        keyword_patterns = {
            "Appeal(s) Allowed": [
                r"\bappeal(s)?\s+allowed\b",
                r"\bappeal(s)?\s+(is|are|was|were)\s+allowed\b",
                r"\bappeal(s)?\s+succeed(s)?\b"
            ],
            "Appeal(s) Dismissed": [
                r"\bappeal(s)?\s+dismissed\b",
                r"\bappeal(s)?\s+(is|are|was|were)\s+dismissed\b",
                r"\bappeal(s)?\s+fail(s)?\b"
            ],
            "Appeal(s) Disposed Of": [
                r"\bappeal(s)?\s+disposed\s+of\b",
                r"\bappeal(s)?\s+(is|are|was|were)\s+disposed\s+of\b"
            ],
            "Case(s) Allowed": [
                r"\b(case(s)?|petition(s)?)\s+allowed\b",
                r"\b(case(s)?|petition(s)?)\s+(is|are|was|were)\s+allowed\b"
            ],
            "Case(s) Partially Allowed": [
                r"\b(case(s)?|petition(s)?)\s+partially\s+allowed\b",
                r"\b(case(s)?|petition(s)?)\s+(is|are|was|were)\s+partially\s+allowed\b"
            ],
            "Case(s) Dismissed": [
                r"\b(case(s)?|petition(s)?)\s+dismissed\b",
                r"\b(case(s)?|petition(s)?)\s+(is|are|was|were)\s+dismissed\b"
            ],
            "Case(s) Disposed Of": [
                r"\b(case(s)?|petition(s)?)\s+disposed\s+of\b",
                r"\b(case(s)?|petition(s)?)\s+(is|are|was|were)\s+disposed\s+of\b"
            ],
            "Case(s) Remanded": [
                r"\b(case(s)?|petition(s)?)\s+remanded\b",
                r"\b(case(s)?|petition(s)?)\s+(is|are|was|were)\s+remanded\b"
            ],
            "Case(s) Remitted Back": [
                r"\b(case(s)?|petition(s)?)\s+remitted\s+back\b",
                r"\b(case(s)?|petition(s)?)\s+(is|are|was|were)\s+remitted\s+back\b"
            ],
            "Directions Issued": [
                r"\bdirection(s)?\s+issued\b",
                r"\bdirective(s)?\s+issued\b",
                r"\border(s)?\s+issued\s+to\b",
                r"\bdirection(s)?\s+(are|were)\s+issued\b"
            ],
            "Matter Referred to Larger Bench": [
                r"\bmatter\s+referred\s+to\s+larger\s+bench\b",
                r"\breferred\s+to\s+a\s+larger\s+bench\b",
                r"\bmatter\s+(is|was)\s+referred\s+to\s+larger\s+bench\b"
            ],
            "Impugned Order Set Aside": [
                r"\bimpugned\s+(order|judgment)\s+set\s+aside\b",
                r"\bimpugned\s+(order|judgment)\s+quashed\b"
            ],
            "Impugned Order Upheld": [
                r"\bimpugned\s+(order|judgment)\s+upheld\b",
                r"\bimpugned\s+(order|judgment)\s+affirmed\b"
            ]
        }
        
        # Add pattern for explicit "Result of the case:"
        result_pattern = r"\bResult\s+of\s+the\s+case:\b"
        
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        last_50_sentences = sentences[-50:] if len(sentences) > 50 else sentences
        
        # Track if any outcome is found
        outcome_found = False
        matching_sentences = []
        
        # First, check for explicit "Result of the case:"
        for sentence in reversed(last_50_sentences):
            if re.search(result_pattern, sentence, re.IGNORECASE):
                # Extract the part after "Result of the case:"
                match = re.search(result_pattern, sentence, re.IGNORECASE)
                if match:
                    result_text = sentence[match.end():].strip()
                    case_result = f"Result of the case: {result_text}."
                    logger.info(f"Explicit case result found: {case_result}")
                    return {"case_result": case_result}
        
        # If not found, extract specific outcomes
        for sentence in reversed(last_50_sentences):
            if is_reference_text(sentence):
                continue
            matched = False
            for patterns in keyword_patterns.values():
                for pattern in patterns:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        matched = True
                        break
                if matched:
                    break
            if matched:
                matching_sentences.append(sentence)
                outcome_found = True
        
        if outcome_found:
            # Since we reversed, reverse back to original order
            matching_sentences = list(reversed(matching_sentences))
            case_result = "Result of the case: " + ". ".join(matching_sentences) + "."
        else:
            # Fallback: take last 4 non-reference sentences
            non_reference_sentences = [s for s in reversed(last_50_sentences) if not is_reference_text(s)]
            last_few = non_reference_sentences[:4]
            if last_few:
                case_result = "Result of the case: " + ". ".join(reversed(last_few)) + "."
                logger.info(f"Fallback result extracted: {case_result[:100]}...")
            else:
                case_result = "Not Found"
        
        logger.info(f"Extracted case result from {pdf_path}: {case_result}")
        return {"case_result": case_result}
    except Exception as e:
        logger.error(f"Error extracting case result from {pdf_path}: {e}")
        return {"case_result": str(e)}