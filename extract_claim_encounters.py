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

TARGET_GUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'
START_DATE = '2026-01-27'
OUTPUT_JSONL = 'eras_extracted.jsonl'
OUTPUT_CLAIMS_CSV = 'claims_extracted.csv'
OUTPUT_LINES_CSV = 'service_lines.csv'

def extract_all_eras():
    conn = get_connection()
    cursor = conn.cursor()
    
    logger.info(f"Querying ERA records for Practice GUID: {TARGET_GUID} since {START_DATE}")
    
    query = f"""
    SELECT FILERECEIVEDATE, FILENAME, FILECONTENTS, SOURCENAME
    FROM PM_CLEARINGHOUSERESPONSE 
    WHERE PRACTICEGUID = '{TARGET_GUID}'
      AND CLEARINGHOUSERESPONSEREPORTTYPENAME = 'ERA'
      AND FILERECEIVEDATE >= '{START_DATE}'
    ORDER BY FILERECEIVEDATE DESC
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    logger.info(f"ind {len(rows)} ERA files to process.")
    
    parser = EraParser()
    
    # Open output files
    with open(OUTPUT_JSONL, 'w') as f_json, \
         open(OUTPUT_CLAIMS_CSV, 'w', newline='') as f_claims, \
         open(OUTPUT_LINES_CSV, 'w', newline='') as f_lines:
        
        # CSV Writers
        claim_headers = ['FileName', 'ReceivedDate', 'PayerName', 'ClaimID', 'PayerControlNumber', 
                         'PatientName', 'PatientID', 'ProviderName', 'Status', 'Billed', 'Paid', 'PatResp', 'Adjustments']
        line_headers = ['FileName', 'ClaimID', 'LineID_Ref6R', 'Date', 'ProcCode', 'Billed', 'Paid', 'Units', 'Adjustments']
        
        writer_claims = csv.DictWriter(f_claims, fieldnames=claim_headers)
        writer_lines = csv.DictWriter(f_lines, fieldnames=line_headers)
        
        writer_claims.writeheader()
        writer_lines.writeheader()
        
        success_count = 0
        error_count = 0
        
        for row in rows:
            date_recv, filename, content, source_db = row
            
            # Parse
            parsed = parser.parse(content)
            
            if 'error' in parsed:
                logger.error(f"Failed to parse {filename}: {parsed['error']}")
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
            
    logger.info(f"Extraction Complete. Success: {success_count}, Errors: {error_count}")
    logger.info(f"Outputs: {OUTPUT_JSONL}, {OUTPUT_CLAIMS_CSV}, {OUTPUT_LINES_CSV}")

if __name__ == "__main__":
    extract_all_eras()
