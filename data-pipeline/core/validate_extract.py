import csv
import os
import logging

logger = logging.getLogger(__name__)

def validate_extraction(output_dir):
    """
    Validates integrity of extracted CSVs before loading.
    Checks for:
    1. Orphaned Service Lines (Lines pointing to missing Claims)
    """
    claims_path = os.path.join(output_dir, 'claims_extracted.csv')
    lines_path = os.path.join(output_dir, 'service_lines.csv')
    
    if not os.path.exists(claims_path) or not os.path.exists(lines_path):
        # If files missing, maybe no data found? Check existence.
        logger.warning(f"Validation skipped: CSVs not found in {output_dir}")
        return True

    # Load Claim IDs
    claim_ids = set()
    try:
        with open(claims_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('ClaimID'):
                    claim_ids.add(row['ClaimID'])
    except Exception as e:
         logger.error(f"Failed to read claims CSV: {e}")
         return False

    # Check Lines
    orphans = 0
    total_lines = 0
    try:
        with open(lines_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_lines += 1
                cid = row.get('ClaimID')
                if cid and cid not in claim_ids:
                    orphans += 1
                    if orphans <= 5:
                        logger.error(f"Orphan Line Found! Line Ref: {row.get('LineID_Ref6R')}, Missing Parent Claim: {cid}")
    except Exception as e:
        logger.error(f"Failed to read lines CSV: {e}")
        return False
        
    if orphans > 0:
        logger.error(f"Validation FAILED: Found {orphans} orphaned service lines (out of {total_lines}).")
        return False
        
    logger.info(f"Validation Passed: {total_lines} lines integrity checked against {len(claim_ids)} claims.")
    return True
