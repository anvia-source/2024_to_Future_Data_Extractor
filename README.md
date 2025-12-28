# Legal Document Processing Pipeline - Complete Documentation

## Overview
This pipeline processes Supreme Court PDF judgments and extracts comprehensive legal information using 12 specialized extraction programs. The system processes PDFs in batches and generates structured Excel outputs with detailed legal metadata.

---

## Table of Contents
1. System Architecture
2. Program Details
3. Installation & Setup
4. Usage Guide
5. Output Structure
6. Configuration
7. Error Handling
8. Troubleshooting
9.[Performance

---

## System Architecture

### Pipeline Flow

Main Pipeline (main_pipeline.py)
- Orchestrates all 12 extraction programs
- Processes PDFs in batches
- Generates combined Excel output

Extraction Programs:
1. Program 1 → Legal Details
2. Program 2 → Party Information
3. Program 3 → Judge & Language Info
4. Program 4 → Legal References
5. Program 5 → Citations (Program 5)
6. Program 6 → Acts Extraction
7. Program 7 → Citation (First Page)
8. Program 8 → Background & Case Arising
9. Program 9 → Precedent Citations
10. Program 10 → Crime Information
11. Program 11 → Case Results
12. Program 12 → Case Details

Output:
- Combined Excel files (batch processing)
- Comprehensive legal metadata extraction

---

## Program Details

### Program 1: Legal Details Extraction
File: `program_1.py`

Extracts:
- Case Number
- Other Case Numbers
- Case Title
- Judgment Date, Month, Year
- Headnotes
- Case Arising From
- Document Type (Judgment/Order)
- Judge Names
- Number of Judges
- Page Count

Key Features:
- Advanced headnote extraction using pattern matching
- Handles split titles and multi-line case names
- Extracts date in multiple formats
- Splits headnotes if exceeding Excel cell limit (32,767 chars)

Output Columns:
```
Case No. (Program 1)
Other Case Nos (Program 1)
Case Title (Program 1)
Judgment Date (Program 1)
Month (Program 1)
Year (Program 1)
Headnotes (Program 1)
Headnotes_1 (Program 1)
Case Arising From (Program 1)
Headnote Extraction Method (Program 1)
Type (Program 1)
Judge Names (Program 1)
No. of Judges (Program 1)
Page Count (Program 1)
```

---

### Program 2: Party Information Extraction
File: `program_2.py`

Extracts:
- Citation (SCR format)
- Case Title
- Hearing Dates
- Number of Hearings
- Category (Civil/Criminal/Others)
- Subcategory (Appeal type)
- Party Details (Filer & Against)
- Legal Actions
- Party Identity (Individual/Organization/Government)

Key Features:
- Uses spaCy NLP for entity recognition
- Handles "In Re" cases appropriately
- Detects subcategories from first 7 lines
- Normalizes short forms (e.g., "SLP (Civil)" → "Special Leave Petition (Civil)")

Output Columns:
```
Citation (Program 2)
Case Title (Program 2)
Hearing Dates (Program 2)
Number of Hearings (Program 2)
Category (Program 2)
Subcategory (Program 2)
Party Details (Program 2) - Filed By
Party Details (Program 2) - Against Who
Party Details (Program 2) - Filer Action
Party Details (Program 2) - Against Action
Party Details (Program 2) - Filer Name
Party Details (Program 2) - Against Name
Party Details (Program 2) - Filer Identity
Party Details (Program 2) - Against Identity
```

---

### Program 3: Judge & Language Information
File: `program_3.py`

Extracts:
- Section (Law Mentioned)
- Language of Document
- Country

Key Features:
- Extracts legal sections using regex and spaCy
- Detects document language using langdetect
- Default country: India

Output Columns:
```
Section (Law Mentioned) (Program 3)
Language of the Document (Program 3)
Country (Program 3)
```

---

### Program 4: Legal References
**File:** `program_4.py`

Extracts:
- Acts
- Rules
- Laws
- Procedures (CrPC, CPC)
- Penal Codes (IPC)
- Constitutions

Key Features:
- Categorizes legal references into 6 types
- Conditional law extraction (only if < 5 details in other categories)
- Filters unwanted generic law mentions

Output Columns:
```
Acts (Program 4)
Rules (Program 4)
Laws (Program 4)
Procedures (Program 4)
Penal Codes (Program 4)
Constitutions (Program 4)
```

---

### Program 5: Citations Extraction
File: `program_5.py`

Extracts:
- Citations Found (case names)
- Citation Details (with context)

Key Features:
- Finds case citations in paragraphs
- Provides context for each citation (first 200 chars)
- Removes duplicate citations

Output Columns:
```
Citations Found (Program 5)
Citation Details (Program 5)
```

---

### Program 6: Acts Extraction
File: `program_6.py`

Extracts:
- List of Acts (raw section from PDF)

Key Features:
- Extracts "List of Acts" section verbatim
- Stops at "List of Keywords" or end of section

Output Columns:
```
List of Acts (Program 6)
```

---

### **Program 7: Citation (First Page)**
**File:** `program_7.py`

Extracts:
- Citation from first page of PDF

Key Features:
- OCR fallback using Tesseract if text extraction fails
- Cleans jumbled citations (O→0, I→1, T→7)
- Supports multiple citation formats

Output Columns:
```
Citation (Program 7)
```

---

### **Program 8: Background Information**
**File:** `program_8.py`

Extracts:
- Case Arising From (detailed section)

Key Features:
- Extracts full "Case Arising From" section
- Includes judgment and order details
- Handles multiple fallback patterns

Output Columns:
```
Case Arising From (Program 8)
```

---

### Program 9: Precedent Citations
File: `program_9.py`

Extracts:
- Precedent Citations (referenced case law)

Key Features:
- Skips first page to avoid header/title confusion
- Searches for "List of Citations" section
- Keyword-based fallback extraction
- Filters unwanted sections (List of Acts, Keywords)

Output Columns:
```
Precedent Citations (Program 9)
```

---

### Program 10: Crime Information
File: `program_10.py`

**Extracts:
- Crime against children (Boolean)
- Crime against women (Boolean)

Key Features:
- Pattern matching for crime indicators
- Filters legal jargon and citations
- Context-aware detection (checks for victim context)

Output Columns:
```
Crime against children (Program 10)
Crime against women (Program 10)
```

---

### Program 11: Case Results
**File:** `program_11.py`

Extracts:
- Case outcomes and results

Output Columns:
```
(Depends on program_11.py implementation)
```

---

### Program 12: Case Details
File: `program_12.py`

Extracts:
- Additional case details

Output Columns:
```
(Depends on program_12.py implementation)
```

---

## Installation & Setup

### System Requirements
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- 500MB disk space for dependencies

### Required Libraries

```bash
# Core PDF processing
pip install PyMuPDF==1.23.8
pip install pdfplumber==0.10.3
pip install PyPDF2==3.0.1

# OCR (for Program 7)
pip install pytesseract==0.3.10
pip install pdf2image==1.16.3
pip install Pillow==10.1.0

# NLP
pip install spacy==3.7.2
python -m spacy download en_core_web_sm

# Language detection
pip install langdetect==1.0.9

# Excel handling
pip install pandas==2.1.3
pip install openpyxl==3.1.2
pip install xlsxwriter==3.1.9

# All dependencies
pip install -r requirements.txt
```

### `requirements.txt`
```txt
PyMuPDF==1.23.8
pdfplumber==0.10.3
PyPDF2==3.0.1
pytesseract==0.3.10
pdf2image==1.16.3
Pillow==10.1.0
spacy==3.7.2
langdetect==1.0.9
pandas==2.1.3
openpyxl==3.1.2
xlsxwriter==3.1.9
```

### Additional Setup

For Program 7 (OCR):
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr
sudo apt-get install poppler-utils

# macOS
brew install tesseract
brew install poppler

# Windows
# Download and install from:
# https://github.com/UB-Mannheim/tesseract/wiki
# https://github.com/oschwartz10612/poppler-windows/releases
```

### Project Structure

```
legal_document_pipeline/
│
├── main_pipeline.py          # Main orchestrator
├── program_1.py              # Legal details
├── program_2.py              # Party information
├── program_3.py              # Judge & language
├── program_4.py              # Legal references
├── program_5.py              # Citations
├── program_6.py              # Acts extraction
├── program_7.py              # First page citation
├── program_8.py              # Background
├── program_9.py              # Precedent citations
├── program_10.py             # Crime information
├── program_11.py             # Case results
├── program_12.py             # Case details
├── requirements.txt          # Dependencies
├── pipeline_log.txt          # Auto-generated log
├── processed_files_3.txt     # Processing tracker
│
├── input/                    # PDF input folder
│   └── *.pdf
│
└── output/                   # Excel outputs
    ├── combined_legal_details_batch_1.xlsx
    ├── combined_legal_details_batch_2.xlsx
    └── ...
```

---

## Usage Guide

### Basic Usage

1. Configure Paths in `main_pipeline.py`:
```python
if __name__ == "__main__":
    input_folder = r"D:\path\to\your\pdf\folder"
    output_base_file = r"C:\path\to\output\combined_legal_details.xlsx"
    process_pdfs(input_folder, output_base_file)
```

Important Notes:
- ✅ Output folder is **automatically created** if it doesn't exist
- ✅ No need to manually create output directory
- ⚠️ Ensure the parent drive/path exists (e.g., C:\, D:\)
- ⚠️ Verify you have write permissions on the path

2. Run the Pipeline:
```bash
python main_pipeline.py
```

3. Monitor Progress:
- Console output shows current processing status
- Check `pipeline_log.txt` for detailed logs
- Intermediate files saved with `_temp.xlsx` suffix

### Batch Processing

Default Settings:
- Batch size: 200 PDFs per run
- Maximum PDFs: 700 total
- Auto-resume from last processed file

Adjusting Batch Size:
```python
process_pdfs(input_folder, output_base_file, batch_size=100, max_pdfs=500)
```

Resume Processing:
The pipeline automatically tracks processed files in `processed_files_3.txt`. Just rerun the script to continue from where it stopped.

### Running Individual Programs

Test a single PDF:
```python
from program_1 import extract_legal_details

pdf_path = "path/to/case.pdf"
result = extract_legal_details(pdf_path)
print(result)
```

---

## Output Structure

### Excel File Format

**Naming Convention:**
```
{base_filename}_batch_{number}.xlsx
```

Example: `combined_legal_details_batch_1.xlsx`

### Complete Column List (All Programs)

| Column Name | Source | Description |
|-------------|--------|-------------|
| File Name | Pipeline | PDF filename |
| Case No. (Program 1) | Program 1 | Primary case number |
| Other Case Nos (Program 1) | Program 1 | Additional case numbers |
| Case Title (Program 1) | Program 1 | Full case title |
| Judgment Date (Program 1) | Program 1 | Date of judgment (DD-MM-YYYY) |
| Month (Program 1) | Program 1 | Month name |
| Year (Program 1) | Program 1 | Year (YYYY) |
| Headnotes (Program 1) | Program 1 | Case headnotes (part 1) |
| Headnotes_1 (Program 1) | Program 1 | Overflow headnotes (part 2) |
| Case Arising From (Program 1) | Program 1 | Jurisdiction section |
| Headnote Extraction Method (Program 1) | Program 1 | Method used |
| Type (Program 1) | Program 1 | Judgment/Order |
| Judge Names (Program 1) | Program 1 | Comma-separated judges |
| No. of Judges (Program 1) | Program 1 | Count |
| Page Count (Program 1) | Program 1 | Total pages |
| Citation (Program 2) | Program 2 | SCR citation |
| Case Title (Program 2) | Program 2 | Case title (NLP extracted) |
| Hearing Dates (Program 2) | Program 2 | Comma-separated dates |
| Number of Hearings (Program 2) | Program 2 | Count |
| Category (Program 2) | Program 2 | Civil/Criminal/Others |
| Subcategory (Program 2) | Program 2 | Appeal type |
| Party Details (Program 2) - Filed By | Program 2 | Filer role |
| Party Details (Program 2) - Against Who | Program 2 | Respondent role |
| Party Details (Program 2) - Filer Action | Program 2 | Legal action taken |
| Party Details (Program 2) - Against Action | Program 2 | Response action |
| Party Details (Program 2) - Filer Name | Program 2 | Filer name |
| Party Details (Program 2) - Against Name | Program 2 | Respondent name |
| Party Details (Program 2) - Filer Identity | Program 2 | Individual/Org/Gov |
| Party Details (Program 2) - Against Identity | Program 2 | Individual/Org/Gov |
| Section (Law Mentioned) (Program 3) | Program 3 | Legal sections cited |
| Language of the Document (Program 3) | Program 3 | Document language |
| Country (Program 3) | Program 3 | Country (India) |
| Acts (Program 4) | Program 4 | Acts referenced |
| Rules (Program 4) | Program 4 | Rules referenced |
| Laws (Program 4) | Program 4 | Laws referenced |
| Procedures (Program 4) | Program 4 | CrPC/CPC references |
| Penal Codes (Program 4) | Program 4 | IPC references |
| Constitutions (Program 4) | Program 4 | Constitutional articles |
| Citations Found (Program 5) | Program 5 | Case citations |
| Citation Details (Program 5) | Program 5 | Citation contexts |
| List of Acts (Program 6) | Program 6 | Raw Acts section |
| Citation (Program 7) | Program 7 | First page citation |
| Case Arising From (Program 8) | Program 8 | Detailed background |
| Precedent Citations (Program 9) | Program 9 | Referenced case law |
| Crime against children (Program 10) | Program 10 | Boolean |
| Crime against women (Program 10) | Program 10 | Boolean |
| [Program 11 columns] | Program 11 | Case results |
| [Program 12 columns] | Program 12 | Additional details |
| Processing Status | Pipeline | Success/Error indicator |
| Error (Program X)| Pipeline | Error messages (if any) |

---

## Configuration

### Main Pipeline Settings

In `main_pipeline.py`:
```python
# Batch processing
batch_size = 200          # PDFs per batch
max_pdfs = 700           # Total PDFs to process

# Paths
input_folder = "path/to/pdfs"
output_base_file = "path/to/output.xlsx"

# Logging
logging.basicConfig(
    filename='pipeline_log.txt',
    level=logging.INFO
)
```

### Disk Space Management

Automatic Checks:
- Minimum free space: 100 MB
- Path write validation before processing
- Disk space check before each batch

### Processing Tracker

File: `processed_files_3.txt`
- Tracks successfully processed PDFs
- One filename per line
- Auto-created if not exists
- Enables resume functionality

---

## Error Handling

### Error Types

1. File Access Errors
   - PDF not found
   - Permission denied
   - Corrupted PDF

2. Extraction Errors
   - No text extracted
   - Pattern matching failures
   - Empty results

3. System Errors
   - Low disk space
   - Path not writable
   - Excel save failures

### Error Recovery

Automatic:
- Intermediate saves after each PDF
- Temp files with `_temp.xlsx` suffix
- Continues to next PDF on individual failures

Manual:
- Check `pipeline_log.txt` for error details
- Review temp files for partial results
- Rerun pipeline to retry failed PDFs

### Logging

Log File: `pipeline_log.txt`

Log_Levels:
- INFO: Successful operations
- WARNING: Partial failures
- ERROR: Critical failures

Example Log:
```
2025-12-28 10:30:15 - INFO - Processing case_123.pdf
2025-12-28 10:30:16 - INFO - Program 1 (Legal Details) successful
2025-12-28 10:30:17 - WARNING - Program 2 returned empty result
2025-12-28 10:30:18 - ERROR - Error in Program 4: No text extracted
2025-12-28 10:30:19 - INFO - Batch 1 processed. Results saved to output/batch_1.xlsx
```

---

## Troubleshooting

### Common Issues

#### 1. No Text Extracted from PDF
Symptoms: All programs return "No text extracted"

Solutions:
- Check if PDF is image-based (Program 7 has OCR fallback)
- Verify PDF is not password-protected
- Try opening PDF manually to check integrity
- Ensure PyMuPDF and pdfplumber are correctly installed

#### 2. spaCy Model Not Found
Symptoms: `OSError: [E050] Can't find model 'en_core_web_sm'`

Solution:
```bash
python -m spacy download en_core_web_sm
```

#### 3. Permission Denied (Excel Save)
**Symptoms:** `PermissionError: [Errno 13] Permission denied`

Solutions:
- Close Excel file if it's open
- Check write permissions on output folder
- Run script as administrator (Windows)
- Change output path to user directory

#### 4. Tesseract Not Found (Program 7)
Symptoms: `TesseractNotFoundError`

Solutions:
- Install Tesseract OCR (see Installation section)
- Add Tesseract to system PATH
- Set path explicitly in code:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

#### 5. Low Disk Space Warning
Symptoms: Pipeline stops with disk space error

Solutions:
- Free up at least 100 MB space
- Change output directory to drive with more space
- Delete temporary files

### Debug Mode

Enable detailed logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

Test individual program:
```python
# Add debug prints
print(f"Extracted text length: {len(text)}")
print(f"First 500 chars: {text[:500]}")
```

---

## Performance

### Processing Speed

| Program | Avg Time/PDF | Heavy Operations |
|---------|--------------|------------------|
| Program 1 | 2-4s | Date parsing, headnote extraction |
| Program 2 | 3-5s | spaCy NLP, entity recognition |
| Program 3 | 1-2s | Regex, language detection |
| Program 4 | 1-2s | Multiple regex patterns |
| Program 5 | 1-2s | Citation search |
| Program 6 | 0.5-1s | Simple section extraction |
| Program 7 | 2-10s | OCR (if needed) |
| Program 8 | 1-2s | Section extraction |
| Program 9 | 1-2s | Filtered citation search |
| Program 10 | 1-2s | Pattern matching |
| Program 11 | 1-2s | TBD |
| Program 12 | 1-2s | TBD |

Total Average: 15-30 seconds per PDF

Batch Performance:
- 200 PDFs: 50-100 minutes
- 700 PDFs: 3-6 hours (with 3-4 batch runs)

### Optimization Tips

1. Batch Size:
   - Smaller batches (50-100): Faster individual runs, more restarts
   - Larger batches (200-300): Longer runs, fewer restarts

2. Disk Speed:
   - Use SSD for faster PDF reading
   - Keep temp files on same drive as output

3. RAM:
   - Close unnecessary applications
   - 8GB+ RAM for smooth processing

4. PDF Quality:
   - Text-based PDFs process 10x faster than image PDFs
   - Clean PDFs with standard formatting process faster

---

## Advanced Usage

### Parallel Processing (Future Enhancement)

```python
from multiprocessing import Pool

def process_single_pdf(pdf_path):
    # Run all programs
    results = {}
    for prog, name in programs:
        results.update(prog(pdf_path))
    return results

# Process 4 PDFs simultaneously
with Pool(4) as p:
    results = p.map(process_single_pdf, pdf_list)
```

### Custom Output Format

```python
# Save as CSV instead of Excel
df.to_csv(output_file, index=False)

# Save specific columns only
columns_to_save = ['File Name', 'Case Title (Program 1)', 'Category (Program 2)']
df[columns_to_save].to_excel(output_file, index=False)
```

---

## Support & Maintenance

### Log Analysis

View recent errors:
```bash
grep "ERROR" pipeline_log.txt | tail -20
```

Count processed PDFs:
```bash
wc -l processed_files_3.txt
```

Find PDFs with specific errors:
```bash
grep "Program 10" pipeline_log.txt | grep "ERROR"
```

### Backup & Recovery

Before major runs:
```bash
# Backup processed files list
cp processed_files_3.txt processed_files_backup.txt

# Backup existing outputs
cp -r output/ output_backup/
```

Recovery from crash:
1. Check `pipeline_log.txt` for last processed PDF
2. Check for temp files (`*_temp.xlsx`)
3. Rerun pipeline (auto-resumes from processed_files_3.txt)

---

## Version History

### Version 1.0 (Current)
- ✅ 12 extraction programs integrated
- ✅ Comprehensive logging and error handling
- ✅ Batch processing with auto-resume
- ✅ Intermediate saves for data safety

---

## Future Enhancements

### Planned Features
- [ ] Parallel processing support
- [ ] Web interface for monitoring
- [ ] Database storage option
- [ ] PDF quality assessment
- [ ] Automatic retry for failed extractions
- [ ] Email notifications on batch completion
- [ ] Statistical analysis dashboard
- [ ] Export to JSON/CSV options

---



## Quick Reference

### Essential Commands

```bash
# Install all dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Run pipeline
python main_pipeline.py

# Check logs
tail -f pipeline_log.txt

# View processed count
wc -l processed_files_3.txt

# Test single program
python -c "from program_1 import extract_legal_details; print(extract_legal_details('test.pdf'))"
```

### Key Files
- `main_pipeline.py` - Main orchestrator
- `pipeline_log.txt` - Processing logs
- `processed_files_3.txt` - Progress tracker
- `requirements.txt` - Dependencies

