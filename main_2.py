import os
import pandas as pd
import logging
import time
import re
import traceback
import shutil
from pathlib import Path

# Placeholder imports for extraction programs (replace with actual imports)
from program_1 import extract_legal_details as extract_1
from program_2 import extract_parties as extract_2
from program_3 import extract_judges as extract_3
from program_4 import extract_legal_references as extract_4
from program_6 import extract_acts as extract_6
from program_7 import extract_citation as extract_7
from program_8 import extract_background as extract_8
from program_10 import extract_crime_info as extract_10
from program_11 import extract_case_result as extract_11
from program_12 import extract_case_details as extract_12

logging.basicConfig(
    filename='pipeline_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_disk_space(path):
    """Check available disk space in the output directory."""
    total, used, free = shutil.disk_usage(path)
    free_mb = free / (1024 ** 2)  # Convert to MB
    if free_mb < 100:  # Less than 100 MB
        logger.error(f"Low disk space: {free_mb:.2f} MB available in {path}")
        print(f"Error: Low disk space ({free_mb:.2f} MB) in {path}. Free up space and retry.")
        return False
    return True

def validate_path(path):
    """Validate if the output path is writable."""
    try:
        with open(os.path.join(path, 'test_write.txt'), 'w') as f:
            f.write('test')
        os.remove(os.path.join(path, 'test_write.txt'))
        return True
    except Exception as e:
        logger.error(f"Path {path} is not writable: {str(e)}")
        print(f"Error: Output path {path} is not writable: {str(e)}")
        return False

def get_next_batch_number(output_dir, base_filename):
    """Determine the next batch number based on existing files."""
    pattern = re.compile(rf"{base_filename}_batch_(\d+)\.xlsx")
    batch_numbers = []
    for file in os.listdir(output_dir):
        match = pattern.match(file)
        if match:
            batch_numbers.append(int(match.group(1)))
    return max(batch_numbers, default=0) + 1

def process_pdfs(input_folder, output_base_file, batch_size=200, max_pdfs=700):
    try:
        # Validate input and output paths
        output_dir = os.path.dirname(output_base_file)
        if not validate_path(output_dir):
            return
        if not check_disk_space(output_dir):
            return

        # Get list of PDF files
        pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')][:max_pdfs]
        if not pdf_files:
            logger.error("No PDF files found in the input folder")
            print("No PDF files found in the input folder")
            return
        
        # Check for processed files log
        processed_log = os.path.join(output_dir, 'processed_files_3.txt')
        processed_files = set()
        if os.path.exists(processed_log):
            with open(processed_log, 'r') as f:
                processed_files = set(f.read().splitlines())
        
        # Filter out already processed files
        remaining_files = [f for f in pdf_files if f not in processed_files]
        if not remaining_files:
            logger.info("All PDFs have been processed")
            print("All PDFs have been processed")
            return
        
        # Take next batch
        batch_files = remaining_files[:batch_size]
        all_results = []
        
        for pdf_file in batch_files:
            pdf_path = os.path.join(input_folder, pdf_file)
            logger.info(f"Processing {pdf_file}")
            print(f"Processing {pdf_file}")
            
            result = {"File Name": pdf_file}
            
            programs = [
                (extract_1, "Legal Details"),
                (extract_2, "Parties"),
                (extract_3, "Judges"),
                (extract_4, "Legal References"),
                (extract_6, "Acts"),
                (extract_7, "Citation"),
                (extract_8, "Background"),
                (extract_10, "Crime Info"),
                (extract_11, "Case Outcomes"),
                (extract_12, "Case Details")
            ]
            
            for i, (prog, prog_name) in enumerate(programs, 1):
                try:
                    prog_result = prog(pdf_path)
                    if prog_result is None or not prog_result:
                        logger.warning(f"Program {i} ({prog_name}) returned empty result for {pdf_file}")
                        result[f"Error (Program {i} - {prog_name})"] = "Empty result"
                    else:
                        logger.info(f"Program {i} ({prog_name}) successful for {pdf_file}")
                        result.update(prog_result)
                except Exception as e:
                    logger.error(f"Error in Program {i} ({prog_name}) for {pdf_file}: {str(e)}")
                    result[f"Error (Program {i} - {prog_name})"] = str(e)
            
            all_results.append(result)
            
            # Save intermediate results to avoid data loss
            try:
                intermediate_df = pd.DataFrame(all_results)
                base_filename = os.path.splitext(os.path.basename(output_base_file))[0]
                batch_number = get_next_batch_number(output_dir, base_filename)
                temp_output_file = os.path.join(output_dir, f"{base_filename}_batch_{batch_number}_temp.xlsx")
                intermediate_df.to_excel(temp_output_file, index=False, engine='openpyxl')
                logger.info(f"Intermediate results saved to {temp_output_file} for {pdf_file}")
            except Exception as e:
                logger.error(f"Failed to save intermediate results for {pdf_file}: {str(e)}")
                print(f"Failed to save intermediate results for {pdf_file}: {str(e)}")
            
            # Add to processed files
            with open(processed_log, 'a') as f:
                f.write(pdf_file + '\n')
        
        # Create output directory if it doesn't exist
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Determine output file for this batch
        base_filename = os.path.splitext(os.path.basename(output_base_file))[0]
        batch_number = get_next_batch_number(output_dir, base_filename)
        output_file = os.path.join(output_dir, f"{base_filename}_batch_{batch_number}.xlsx")
        
        # Save final results
        max_retries = 3
        for attempt in range(max_retries):
            try:
                df = pd.DataFrame(all_results)
                logger.info(f"Attempting to save to {output_file} with openpyxl (attempt {attempt + 1})")
                df.to_excel(output_file, index=False, engine='openpyxl')
                logger.info(f"Batch {batch_number} processed. Results saved to {output_file}")
                print(f"Batch {batch_number} of {len(batch_files)} PDFs processed. Results saved to {output_file}")
                print(f"Please restart the program to process the next batch.")
                # Remove temporary file if it exists
                temp_output_file = os.path.join(output_dir, f"{base_filename}_batch_{batch_number}_temp.xlsx")
                if os.path.exists(temp_output_file):
                    os.remove(temp_output_file)
                break
            except PermissionError as pe:
                logger.error(f"Permission denied on attempt {attempt + 1} for {output_file}: {str(pe)}")
                print(f"Permission denied on attempt {attempt + 1}. Retrying in 5 seconds...")
                time.sleep(5)
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached for {output_file}. Please ensure the file is not open and you have write permissions.")
                    print(f"Max retries reached. Please ensure the file is not open and you have write permissions.")
                    return
            except Exception as e:
                logger.error(f"Unexpected error while saving to {output_file}: {str(e)}\n{traceback.format_exc()}")
                print(f"Unexpected error while saving to {output_file}: {str(e)}")
                # Try with xlsxwriter as a fallback
                if attempt == max_retries - 1:
                    try:
                        logger.info(f"Attempting to save with xlsxwriter as fallback for {output_file}")
                        df.to_excel(output_file, index=False, engine='xlsxwriter')
                        logger.info(f"Batch {batch_number} processed. Results saved to {output_file} using xlsxwriter")
                        print(f"Batch {batch_number} of {len(batch_files)} PDFs processed. Results saved to {output_file} using xlsxwriter")
                        temp_output_file = os.path.join(output_dir, f"{base_filename}_batch_{batch_number}_temp.xlsx")
                        if os.path.exists(temp_output_file):
                            os.remove(temp_output_file)
                        break
                    except Exception as e2:
                        logger.error(f"Failed to save with xlsxwriter to {output_file}: {str(e2)}\n{traceback.format_exc()}")
                        print(f"Failed to save with xlsxwriter to {output_file}: {str(e2)}")
                        print(f"Data was not saved. Check {temp_output_file} for intermediate results.")
                        return
    
    except Exception as e:
        logger.error(f"Error in pipeline execution: {str(e)}\n{traceback.format_exc()}")
        print(f"Error in pipeline execution: {str(e)}")

if __name__ == "__main__":
    input_folder = r"D:\ANVIA_PRODUCT_FILES\2025_sc\splitted_cases_2025\2025_judg_order\Judgment\civil\test_26_12_2025"
    output_base_file = r"C:\Users\Roshan\Downloads\my_flask_app\output\combined_legal_details_2025_civil_test_26_12_2025.xlsx"
    process_pdfs(input_folder, output_base_file)