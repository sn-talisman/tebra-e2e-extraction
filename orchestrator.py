import os
import logging
from src.connection import get_connection

# Import Pipeline Steps
from extract_claim_encounters import extract_all_eras
from extract_batch_optimized import extract_batch
from load_to_postgres import load_practice_data

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Orchestrator')

import csv
import time
from datetime import datetime

# ... imports ...

# ... imports ...

OUTPUT_ROOT = 'output_all_practices'
REPORT_FILE = 'execution_report.md'

def get_practices():
    """Get all practices that have clearinghouse response data, regardless of ACTIVE status."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Include ACTIVE practices with clearinghouse data
        cursor.execute("""
            SELECT DISTINCT p.PRACTICEGUID, p.NAME 
            FROM PM_PRACTICE p
            WHERE p.ACTIVE = TRUE
            AND EXISTS (
                SELECT 1 FROM PM_CLEARINGHOUSERESPONSE c 
                WHERE c.PRACTICEGUID = p.PRACTICEGUID
            )
            ORDER BY 
                CASE WHEN p.NAME ILIKE 'Performance%' THEN 0 ELSE 1 END, 
                p.NAME
        """)
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Failed to fetch practices: {e}")
        return []
    finally:
        conn.close()

def sanitize(name):
    return "".join([c for c in name if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')

class PracticeStats:
    def __init__(self, name, guid):
        self.name = name
        self.guid = guid
        self.status = 'Pending'
        self.start_time = None
        self.end_time = None
        self.era_count = 0
        self.lines_extracted = 0
        self.lines_enriched = 0
        self.db_load_status = 'Skipped'
        self.duration_sec = 0
        self.error_msg = ''

def count_file_lines(filepath):
    """Returns number of lines in file."""
    if not os.path.exists(filepath): return 0
    try:
        count = 0
        with open(filepath, 'r') as f:
            count = sum(1 for _ in f)
        
        # If CSV, subtract header
        if filepath.lower().endswith('.csv') and count > 0:
            return count - 1
        return count
    except:
        return 0

def generate_report(stats_list):
    with open(REPORT_FILE, 'w') as f:
        f.write("# Tebra E2E Extraction - Execution Report\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary
        total = len(stats_list)
        success = sum(1 for s in stats_list if s.status == 'Success')
        failed = sum(1 for s in stats_list if s.status == 'Failed')
        total_lines = sum(s.lines_enriched for s in stats_list)
        
        f.write(f"## Summary\n")
        f.write(f"- **Total Practices:** {total}\n")
        f.write(f"- **Success:** {success}\n")
        f.write(f"- **Failed:** {failed}\n")
        f.write(f"- **Total Service Lines Processed:** {total_lines:,}\n\n")
        
        # Table
        f.write("## Detailed Breakdown\n")
        f.write("| Practice Name | Status | Duration | ERAs Found | Lines Extracted | DB Load |\n")
        f.write("|---|---|---|---|---|---|\n")
        for s in stats_list:
            f.write(f"| {s.name} | {s.status} | {s.duration_sec:.1f}s | {s.era_count} | {s.lines_enriched} | {s.db_load_status} |\n")
            
        # Errors
        if failed > 0:
            f.write("\n## Error Logs\n")
            for s in stats_list:
                if s.status == 'Failed':
                    f.write(f"### {s.name}\n")
                    f.write(f"```\n{s.error_msg}\n```\n")

    logger.info(f"Report generated: {os.path.abspath(REPORT_FILE)}")

def run_pipeline():
    practices = get_practices()
    total_practices = len(practices)
    logger.info(f"Found {total_practices} practices to process.")
    
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    stats_list = []
    
    for i, (p_guid, p_name) in enumerate(practices, 1):
        stats = PracticeStats(p_name, p_guid)
        stats.start_time = time.time()
        stats_list.append(stats)
        
        logger.info(f"[{i}/{total_practices}] Processing {p_name}...")
        
        MAX_RETRIES = 1 # Allow 1 retry per practice
        for attempt in range(MAX_RETRIES + 1):
            try:
                folder_name = f"{sanitize(p_name)}_{p_guid}"
                practice_dir = os.path.join(OUTPUT_ROOT, folder_name)
                
                # Step 0: Cleanup (if retrying)
                if attempt > 0:
                    import shutil
                    logger.warning(f"  ... Retrying {p_name} (Attempt {attempt+1}/{MAX_RETRIES+1}). Cleaning {practice_dir}...")
                    if os.path.exists(practice_dir): shutil.rmtree(practice_dir)

                # Step 1: Extract ERAs
                from datetime import timedelta
                start_dt = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                logger.info(f"  > Step 1: Extracting ALL Clearinghouse Responses (Since {start_dt})...")
                
                extract_all_eras(p_guid, start_date=start_dt, output_dir=practice_dir)
                
                stats.era_count = count_file_lines(os.path.join(practice_dir, 'eras_extracted.jsonl')) + 1 
                # Note: count_file_lines currently adds robustness for CSVs but jsonl has no header. 
                # This +1 is a heuristic artifact. Keeping for consistency with report.

                stats.lines_extracted = count_file_lines(os.path.join(practice_dir, 'service_lines.csv'))
                logger.info(f"    -> Found {stats.era_count} ERAs, {stats.lines_extracted} Lines.")

                # Step 1.5: Validation
                from validate_extract import validate_extraction
                if stats.lines_extracted > 0:
                    logger.info("  > Step 1.5: Validating CSV Integrity...")
                    if not validate_extraction(practice_dir):
                        raise Exception("Extraction Validation Failed (Orphan Lines Detectected)")

                # Step 2: Batch Enrichment
                logger.info(f"  > Step 2: Batch Enrichment...")
                if stats.lines_extracted > 0:
                    extract_batch(input_dir=practice_dir, output_dir=practice_dir)
                    stats.lines_enriched = count_file_lines(os.path.join(practice_dir, 'encounters_enriched_deterministic.csv'))
                    logger.info(f"    -> Enriched {stats.lines_enriched} Encounters/Lines.")
                else:
                    logger.warning("    -> Skipping (No Data).")
                
                # Step 3: Load to Postgres
                logger.info(f"  > Step 3: Loading to Postgres...")
                # Always try to load ERA reports, even if no enriched encounter data
                era_reports_file = os.path.join(practice_dir, 'era_reports.csv')
                if stats.lines_enriched > 0 or os.path.exists(era_reports_file):
                    load_practice_data(
                        data_dir=practice_dir, 
                        practice_guid=p_guid,
                        practice_name=p_name,
                        era_only=(stats.lines_enriched == 0)
                    )
                    stats.db_load_status = 'Success' if stats.lines_enriched > 0 else 'ERA Only'
                else:
                    stats.db_load_status = 'No Data'
                
                stats.status = 'Success'
                break # Success, exit retry loop
                
            except Exception as e:
                logger.error(f"  !!! FAILED (Attempt {attempt+1}): {str(e)}")
                if attempt == MAX_RETRIES:
                    stats.status = 'Failed'
                    stats.error_msg = str(e)
                else:
                   time.sleep(2) # Backoff slightly
                
            finally:
                if attempt == MAX_RETRIES or stats.status == 'Success':
                    stats.end_time = time.time()
                    stats.duration_sec = stats.end_time - stats.start_time
                    logger.info(f"  > Finished in {stats.duration_sec:.2f}s")
            
    generate_report(stats_list)

if __name__ == "__main__":
    run_pipeline()
