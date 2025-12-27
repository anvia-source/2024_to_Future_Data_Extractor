import pdfplumber
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Extract text from the PDF, skipping the top of the first page
def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                if page_text:
                    if page_num == 0:
                        lines = page_text.split("\n")
                        filtered_lines = []
                        skip = True
                        for line in lines:
                            if re.search(r"\b(S\.C\.R\.|Supreme Court Reports|\[\d{4}\]\s+\d+\s+S\.C\.R\.|Digital Supreme Court Reports)\b", line, re.IGNORECASE) or \
                               re.search(r"(Writ Petition|Civil Original Jurisdiction|Under Article \d+)", line, re.IGNORECASE) or \
                               re.search(r"\b\d{4}\b.*(v\.|vs\.).*\b\d{4}\b", line, re.IGNORECASE) or \
                               re.search(r"\b(JJ\.|J\.|Justices?|Judges?)\b", line, re.IGNORECASE) or \
                               re.search(r"\b(Adv\.|Advocates?|Sr\. Advs\.|ASG|Dy\. Adv\. Gen\.)\b", line, re.IGNORECASE) or \
                               re.search(r"\b(O R D E R|ORDER)\b", line, re.IGNORECASE):
                                continue
                            if not skip or not re.search(r"^\s*(\[\d{4}\]|\d+\s+S\.C\.R\.|Digital|Supreme|\b\d+\b|v\.|vs\.|Writ|Jurisdiction|Article|Adv\.|JJ\.|J\.)", line, re.IGNORECASE):
                                skip = False
                                filtered_lines.append(line)
                        page_text = "\n".join(filtered_lines)
                    if page_text.strip():
                        text += page_text + "\n"
        if not text.strip():
            logger.warning(f"No text extracted from PDF {pdf_path}.")
            return ""
        logger.info(f"Extracted {len(text)} characters from PDF {pdf_path}.")
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
        return ""

# Split text into paragraphs
def split_into_paragraphs(text: str) -> list:
    if not text or text.strip() == "":
        return []
    paragraphs = re.split(
        r'(?:\n\s*(\d+\.\s+))|(?:\n{2,})|(?=(?:Judgment|Appearances|Facts|Background|Issue|List of Citations and Other References|Case Law Cited|List of Acts|List of Keywords)\b)',
        text
    )
    return [p.strip() for p in paragraphs if p and p.strip()]

# Extract precedent citations
def extract_citations(pdf_path: str) -> dict:
    try:
        text = extract_text_from_pdf(pdf_path)
        if not text:
            return {"Precedent Citations (Program 9)": "No text extracted from PDF"}

        paragraphs = split_into_paragraphs(text)
        if not paragraphs:
            return {"Precedent Citations (Program 9)": "No paragraphs extracted from PDF"}

        details = {"Precedent Citations (Program 9)": "Not found"}

        # Patterns for titles and unwanted sections
        patterns = {
            "Citations": r"(List of Citations and Other References|Case Law Cited)\b",
            "Unwanted": r"(List of Acts|List of Keywords)\b"
        }

        # Keywords for identifying citations
        citation_keywords = [
            r"\b(SCR|SCC)\b",
            r"\[\d{4}\]",
            r"\b(referred to|relied on|distinguished|overruled|cited)\b",
            r"\d+\s+S\.C\.R\.",
            r"\(\d{4}\)",
        ]

        # Step 1: Extract Citations using title
        citations_paragraphs = []
        for i, para in enumerate(paragraphs):
            if re.search(patterns["Citations"], para, re.IGNORECASE):
                for j in range(i + 1, len(paragraphs)):
                    if not re.match(r'^\s*\d+\.\s+', paragraphs[j]) and not re.search(r'^(Judgment|Appearances|Facts|Background|Issue|List of Acts|List of Keywords)', paragraphs[j], re.IGNORECASE):
                        citations_paragraphs.append(paragraphs[j])
                    else:
                        break
                break

        if citations_paragraphs:
            details["Precedent Citations (Program 9)"] = "\n".join(citations_paragraphs)
            logger.info(f"Extracted citations from {pdf_path}: {citations_paragraphs[0][:100]}...")
        else:
            # Step 2: Fallback to keyword-based extraction
            citation_candidates = []
            for para in paragraphs:
                para_lower = para.lower()
                if any(re.search(pattern, para_lower) for pattern in citation_keywords) and \
                   (re.search(r"\b(SCR|SCC)\b", para_lower) or re.search(r"\b(referred to|relied on|distinguished|overruled|cited)\b", para_lower)):
                    if not re.search(patterns["Unwanted"], para, re.IGNORECASE) and \
                       not re.search(r"\b(Writ Petition|Civil Original Jurisdiction)\b", para, re.IGNORECASE):
                        citation_candidates.append(para)

            if citation_candidates:
                def count_citation_patterns(para):
                    return sum(1 for pattern in citation_keywords if re.search(pattern, para.lower()))
                best_candidates = sorted(citation_candidates, key=lambda p: (count_citation_patterns(p), len(p)), reverse=True)
                details["Precedent Citations (Program 9)"] = "\n".join(best_candidates)
                logger.info(f"Extracted keyword-based citations from {pdf_path}: {best_candidates[0][:100]}...")

        return details
    except Exception as e:
        logger.error(f"Error in Program 9 for {pdf_path}: {e}")
        return {"Precedent Citations (Program 9)": f"Error: {str(e)}"}