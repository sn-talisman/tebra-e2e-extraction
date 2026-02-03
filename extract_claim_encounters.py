"""
Batch Extraction Script: ERA Claims & Encounters.
Queries all ERAs for target practice, parses them, and outputs CSV/JSONL.
"""
import json
import csv
import logging
from src.connection import get_connection
from src.era_parser_xml import EraParser

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Refactored for Orchestration
def extract_all_eras(practice_guid, start_date='2015-01-01', output_dir='.'):
    conn = get_connection()
    cursor = conn.cursor()
    
    logger.info(f"Querying ERA records for Practice GUID: {practice_guid} since {start_date}")
    
    query = f"""
    SELECT FILERECEIVEDATE, FILENAME, FILECONTENTS, SOURCENAME, CLEARINGHOUSERESPONSEREPORTTYPENAME
    FROM PM_CLEARINGHOUSERESPONSE 
    WHERE PRACTICEGUID = '{practice_guid}'
      AND CLEARINGHOUSERESPONSEREPORTTYPENAME IN ('ERA', 'Processing')
      AND FILERECEIVEDATE >= '{start_date}'
    ORDER BY FILERECEIVEDATE DESC
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    logger.info(f"Found {len(rows)} ERA files to process.")
    
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    jsonl_path = os.path.join(output_dir, 'eras_extracted.jsonl')
    claims_csv = os.path.join(output_dir, 'claims_extracted.csv')
    lines_csv  = os.path.join(output_dir, 'service_lines.csv')
    reject_csv = os.path.join(output_dir, 'rejections.csv')
    
    parser = EraParser()
    
    # Open output files
    with open(jsonl_path, 'w') as f_json, \
         open(claims_csv, 'w', newline='') as f_claims, \
         open(lines_csv, 'w', newline='') as f_lines, \
         open(reject_csv, 'w', newline='') as f_reject:
        
        # CSV Writers
        claim_headers = ['FileName', 'ReceivedDate', 'PayerName', 'ClaimID', 'PayerControlNumber', 
                         'PatientName', 'PatientID', 'ProviderName', 'Status', 'Billed', 'Paid', 'PatResp', 'Adjustments']
        writer_claims = csv.DictWriter(f_claims, fieldnames=claim_headers)
        writer_claims.writeheader()
        
        line_headers = ['FileName', 'ClaimID', 'LineID_Ref6R', 'Date', 'ProcCode', 'Billed', 'Paid', 'Units', 'Adjustments']
        writer_lines = csv.DictWriter(f_lines, fieldnames=line_headers)
        writer_lines.writeheader()
        
        reject_headers = ['ReceivedDate', 'FileName', 'Type', 'ContentSnippet']
        writer_reject = csv.DictWriter(f_reject, fieldnames=reject_headers)
        writer_reject.writeheader()
        
        success_count = 0
        error_count = 0
        rej_count = 0
        
        for row in rows:
            date_recv, filename, content, source_db, report_type = row
            
            # --- Type A: Processing / Rejection ---
            if report_type != 'ERA':
                snippet = content[:500].replace('\n', ' ').replace('\r', '') if content else ""
                writer_reject.writerow({
                    'ReceivedDate': date_recv,
                    'FileName': filename,
                    'Type': report_type,
                    'ContentSnippet': snippet
                })
                rej_count += 1
                continue
            
            # --- Type B: ERA Parsing ---
            try:
                # Parse
                parsed = parser.parse(content)
                
                if 'error' in parsed:
                    # Treat XML errors as rejections/failures for now? Or just log error
                    logger.warning(f"Failed to parse ERA {filename}: {parsed['error']}")
                    error_count += 1
                    continue
                
                # Metadata injection for JSONL
                parsed['_metadata'] = {
                    'filename': filename,
                    'received_date': str(date_recv),
                    'source_db': source_db
                }
                
                # Write JSONL
                f_json.write(json.dumps(parsed) + "\n")
                
                # Write CSVs
                # Claims Loop
                for c in parsed.get('claims', []):
                    # Clean Adjustments
                    c_adjs = "; ".join(c.get('adjustments', []))
                    
                    # Write Claim Row
                    writer_claims.writerow({
                        'FileName': filename,
                        'ReceivedDate': date_recv,
                        'PayerName': parsed.get('payer', {}).get('name', 'Unknown'),
                        'ClaimID': c.get('claim_id', ''),
                        'PayerControlNumber': c.get('payer_control_number', ''),
                        'PatientName': c.get('patient', {}).get('name', ''),
                        'PatientID': c.get('patient', {}).get('id', ''),
                        'ProviderName': c.get('provider', {}).get('name', ''),
                        'Status': c.get('status_code', ''),
                        'Billed': c.get('charge_amount', '0'),
                        'Paid': c.get('paid_amount', '0'),
                        'PatResp': c.get('patient_resp', '0'),
                        'Adjustments': c_adjs
                    })
                    
                    # Lines Loop
                    for svc in c.get('service_lines', []):
                        # Extract REF 6R
                        line_ref = ""
                        if 'refs' in svc:
                            for r in svc['refs']:
                                if r['type'] == '6R':
                                    # Heuristic: Extract the embedded ID if it looks like Tebra's S...K123456K9 format
                                    # Or just use raw value if simple
                                    import re
                                    match = re.search(r'K(\d{6})[A-Z0-9]*$', r['value'])
                                    if match:
                                        line_ref = match.group(1)
                                    else:
                                        line_ref = r['value']
                                    break
                        
                        s_adjs = "; ".join(svc.get('adjustments', []))
                        
                        writer_lines.writerow({
                            'FileName': filename,
                            'ClaimID': c.get('claim_id', ''),
                            'LineID_Ref6R': line_ref,
                            'Date': svc.get('date', ''),
                            'ProcCode': svc.get('proc_code', ''),
                            'Billed': svc.get('charge', '0'),
                            'Paid': svc.get('paid', '0'),
                            'Units': svc.get('units', ''),
                            'Adjustments': s_adjs
                        })
                
                success_count += 1
            except Exception as e:
                logger.error(f"Error checking {filename}: {e}")
                error_count += 1
            
            # Critical: Flush buffers to disk after each file to prevent corruption
            f_claims.flush()
            f_lines.flush()
            f_reject.flush()
            # Optional: os.fsync for durability if needed, but flush is usually enough for app crashes
            # os.fsync(f_claims.fileno()) 
    logger.info(f"Extraction Complete. ERAs: {success_count}, Rejections: {rej_count}, Errors: {error_count}")
            
    logger.info(f"Extraction Complete. Success: {success_count}, Errors: {error_count}")

if __name__ == "__main__":
    # Test Run for target practice
    extract_all_eras('EE5ED349-D9DD-4BF5-81A5-AA503A261961')
