"""
Batch Extraction Script: ERA Claims & Encounters.
Queries ALL clearinghouse responses for target practice, parses ERAs, and outputs CSV/JSONL.
Updated: 2026-02-04 - Pulls all columns from PM_CLEARINGHOUSERESPONSE
"""
import json
import csv
import logging
import hashlib
import os
import re
from src.connection import get_connection
from src.era_parser_xml import EraParser

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_all_eras(practice_guid, start_date='2025-08-01', output_dir='.'):
    """
    Extract all clearinghouse responses for a practice.
    Now pulls ALL columns from PM_CLEARINGHOUSERESPONSE.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    logger.info(f"Querying ALL Clearinghouse Responses for Practice GUID: {practice_guid} since {start_date}")
    
    # Updated query: ALL columns, NO type filter
    query = f"""
    SELECT 
        CUSTOMERID,
        CLEARINGHOUSERESPONSEID,
        CLEARINGHOUSERESPONSEREPORTTYPEID,
        CLEARINGHOUSERESPONSEREPORTTYPENAME,
        CLEARINGHOUSERESPONSESOURCETYPEID,
        CLEARINGHOUSERESPONSESOURCETYPENAME,
        DENIED,
        FILECONTENTS,
        FILENAME,
        FILERECEIVEDATE,
        ITEMCOUNT,
        PAYMENTID,
        PRACTICEGUID,
        PROCESSEDFLAG,
        REJECTED,
        RESPONSETYPE,
        CLEARINGHOUSERESPONSETYPENAME,
        REVIEWEDFLAG,
        SOURCEADDRESS,
        SOURCENAME,
        TITLE,
        TOTALAMOUNT
    FROM PM_CLEARINGHOUSERESPONSE 
    WHERE PRACTICEGUID = '{practice_guid}'
      AND FILERECEIVEDATE >= '{start_date}'
    ORDER BY FILERECEIVEDATE DESC
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    logger.info(f"Found {len(rows)} Clearinghouse Response records to process.")
    
    os.makedirs(output_dir, exist_ok=True)
    
    jsonl_path = os.path.join(output_dir, 'eras_extracted.jsonl')
    claims_csv = os.path.join(output_dir, 'claims_extracted.csv')
    lines_csv  = os.path.join(output_dir, 'service_lines.csv')
    reject_csv = os.path.join(output_dir, 'rejections.csv')
    reports_csv = os.path.join(output_dir, 'era_reports.csv')
    
    parser = EraParser()
    
    # Updated headers with ALL Snowflake columns
    report_headers = [
        'EraReportID', 'ClearinghouseResponseID', 'CustomerID',
        'FileName', 'ReceivedDate', 
        'ReportTypeID', 'ReportTypeName',
        'SourceTypeID', 'SourceTypeName',
        'PayerName', 'PayerID', 'CheckNumber', 'CheckDate', 
        'TotalPaid', 'TotalAmount', 'Method', 'PracticeGUID',
        'DeniedCount', 'RejectedCount', 'ClaimCount',
        'PaymentID', 'ProcessedFlag', 'ResponseType', 'ResponseTypeName',
        'ReviewedFlag', 'SourceAddress', 'Title'
    ]
    
    claim_headers = [
        'EraReportID', 'FileName', 'ReceivedDate', 'PayerName', 
        'ClaimID', 'PayerControlNumber', 
        'PatientName', 'PatientID', 'ProviderName', 
        'Status', 'Billed', 'Paid', 'PatResp', 'Adjustments'
    ]
    
    line_headers = [
        'FileName', 'ClaimID', 'LineID_Ref6R', 
        'Date', 'ProcCode', 'Billed', 'Paid', 'Units', 'Adjustments', 'Status'
    ]
    
    reject_headers = ['ReceivedDate', 'FileName', 'Type', 'ContentSnippet']
    
    with open(jsonl_path, 'w') as f_json, \
         open(claims_csv, 'w', newline='') as f_claims, \
         open(lines_csv, 'w', newline='') as f_lines, \
         open(reject_csv, 'w', newline='') as f_reject, \
         open(reports_csv, 'w', newline='') as f_reports:
        
        writer_reports = csv.DictWriter(f_reports, fieldnames=report_headers)
        writer_reports.writeheader()
        
        writer_claims = csv.DictWriter(f_claims, fieldnames=claim_headers)
        writer_claims.writeheader()
        
        writer_lines = csv.DictWriter(f_lines, fieldnames=line_headers)
        writer_lines.writeheader()
        
        writer_reject = csv.DictWriter(f_reject, fieldnames=reject_headers)
        writer_reject.writeheader()
        
        success_count = 0
        error_count = 0
        rej_count = 0
        
        for row in rows:
            # Unpack all 22 columns
            (customer_id, ch_response_id, report_type_id, report_type_name,
             source_type_id, source_type_name, denied_cnt, content, filename,
             date_recv, item_count, payment_id, prac_guid, processed_flag,
             rejected_cnt, response_type, response_type_name, reviewed_flag,
             source_address, source_name, title, total_amount) = row
            
            # Use Snowflake's ID as primary key (fallback to hash if null)
            rid = ch_response_id if ch_response_id else hashlib.md5(f"{filename}{date_recv}".encode()).hexdigest()
            
            # --- Type A: Non-ERA (Processing, Rejection, Acknowledgment, etc.) ---
            if report_type_name not in ('ERA',):
                snippet = content[:500].replace('\n', ' ').replace('\r', '') if content else ""
                writer_reject.writerow({
                    'ReceivedDate': date_recv,
                    'FileName': filename,
                    'Type': report_type_name,
                    'ContentSnippet': snippet
                })
                rej_count += 1
                
                # Still write to era_reports for completeness
                writer_reports.writerow({
                    'EraReportID': rid,
                    'ClearinghouseResponseID': ch_response_id,
                    'CustomerID': customer_id,
                    'FileName': filename,
                    'ReceivedDate': date_recv,
                    'ReportTypeID': report_type_id,
                    'ReportTypeName': report_type_name,
                    'SourceTypeID': source_type_id,
                    'SourceTypeName': source_type_name,
                    'PayerName': source_name or 'Unknown',
                    'PayerID': '',
                    'CheckNumber': '',
                    'CheckDate': '',
                    'TotalPaid': 0,
                    'TotalAmount': total_amount or 0,
                    'Method': '',
                    'PracticeGUID': prac_guid,
                    'DeniedCount': denied_cnt or 0,
                    'RejectedCount': rejected_cnt or 0,
                    'ClaimCount': item_count or 0,
                    'PaymentID': payment_id,
                    'ProcessedFlag': processed_flag,
                    'ResponseType': response_type,
                    'ResponseTypeName': response_type_name,
                    'ReviewedFlag': reviewed_flag,
                    'SourceAddress': source_address,
                    'Title': title
                })
                continue
            
            # --- Type B: ERA Parsing ---
            try:
                parsed = parser.parse(content)
                
                if 'error' in parsed:
                    logger.warning(f"Failed to parse ERA {filename}: {parsed['error']}")
                    error_count += 1
                    continue
                
                # Metadata injection for JSONL
                parsed['_metadata'] = {
                    'filename': filename,
                    'received_date': str(date_recv),
                    'clearinghouse_response_id': ch_response_id,
                    'source_db': source_name
                }
                parsed['id'] = rid
                
                # Extract parsed payment info
                payment = parsed.get('payment', {})
                payer = parsed.get('payer', {})
                
                # Write Report with ALL fields
                writer_reports.writerow({
                    'EraReportID': rid,
                    'ClearinghouseResponseID': ch_response_id,
                    'CustomerID': customer_id,
                    'FileName': filename,
                    'ReceivedDate': date_recv,
                    'ReportTypeID': report_type_id,
                    'ReportTypeName': report_type_name,
                    'SourceTypeID': source_type_id,
                    'SourceTypeName': source_type_name,
                    'PayerName': payer.get('name', source_name or 'Unknown Payer'),
                    'PayerID': payer.get('id', ''),
                    'CheckNumber': payment.get('check_number', ''),
                    'CheckDate': payment.get('date', ''),
                    'TotalPaid': payment.get('total_paid', 0),
                    'TotalAmount': total_amount or 0,
                    'Method': payment.get('method', ''),
                    'PracticeGUID': prac_guid,
                    'DeniedCount': denied_cnt or 0,
                    'RejectedCount': rejected_cnt or 0,
                    'ClaimCount': item_count or 0,
                    'PaymentID': payment_id,
                    'ProcessedFlag': processed_flag,
                    'ResponseType': response_type,
                    'ResponseTypeName': response_type_name,
                    'ReviewedFlag': reviewed_flag,
                    'SourceAddress': source_address,
                    'Title': title
                })

                # Write JSONL
                f_json.write(json.dumps(parsed) + "\n")
                
                # Write Claims
                for c in parsed.get('claims', []):
                    c_adjs = "; ".join(c.get('adjustments', []))
                    
                    writer_claims.writerow({
                        'EraReportID': rid,
                        'FileName': filename,
                        'ReceivedDate': date_recv,
                        'PayerName': payer.get('name', 'Unknown'),
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
                    
                    # Write Service Lines
                    for svc in c.get('service_lines', []):
                        line_ref = ""
                        if 'refs' in svc:
                            for r in svc['refs']:
                                if r['type'] == '6R':
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
                            'Adjustments': s_adjs,
                            'Status': c.get('status_code', '')
                        })
                
                success_count += 1
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                error_count += 1
            
            # Flush buffers
            f_claims.flush()
            f_lines.flush()
            f_reject.flush()
            f_reports.flush()
    
    logger.info(f"Extraction Complete. ERAs: {success_count}, Non-ERA: {rej_count}, Errors: {error_count}")
    return {'success': success_count, 'non_era': rej_count, 'errors': error_count}

if __name__ == "__main__":
    # Default: Single practice test with 6 months lookback
    extract_all_eras('EE5ED349-D9DD-4BF5-81A5-AA503A261961', start_date='2025-08-01')
