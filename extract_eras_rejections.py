"""
Step 2: Get list or ERAs (835) and Rejections
Target: PERFORMANCE REHABILITATION CORP. (EE5ED349-D9DD-4BF5-81A5-AA503A261961)
Query PM_CLEARINGHOUSERESPONSE for ERAs and Rejections.
"""
import json
import io
import re
from src.connection import get_connection

# Constants
TARGET_PRACTICE_GUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'
TARGET_PRACTICE_NAME = 'PERFORMANCE REHABILITATION CORP.'
LOOKBACK_HOURS = 120  # 5 days

def print_debug(msg):
    print(f"[DEBUG] {msg}", flush=True)

def print_table(data, columns):
    if not data:
        print("No data to display table.")
        return

    widths = {col: len(col) for col in columns}
    for row in data:
        for col in columns:
            val = str(row.get(col, ""))
            # Truncate long values for display
            if len(val) > 50:
                val = val[:47] + "..."
            widths[col] = max(widths[col], len(val))

    fmt = " | ".join([f"{{:<{widths[col]}}}" for col in columns])
    separator = "-+-".join(["-" * widths[col] for col in columns])

    print("\n" + fmt.format(*columns))
    print(separator)
    for row in data:
        values = []
        for col in columns:
            val = str(row.get(col, ""))
            if len(val) > 50:
                val = val[:47] + "..."
            values.append(val)
        print(fmt.format(*values))
    print("\n", flush=True)

def parse_835_snippet(file_contents):
    """
    Very basic snippet extractor for 835 content to verify we have data.
    Looking for TRN (Transaction), CLP (Claim), N1 (Entity).
    """
    if not file_contents:
        return {"parsed": False, "reason": "Empty content"}
    
    # 835 is usually segment~segment~ ... check for common terminators
    # This is a naive check for display purposes
    snippet = file_contents[:200].replace('\n', ' ').replace('\r', '')
    
    # Count CLPs
    clp_count = file_contents.count("CLP*")
    
    return {
        "parsed": True,
        "clp_count": clp_count,
        "snippet": snippet
    }

def parse_csr_report(file_contents):
    """
    Parses a Clearinghouse Processing Report (CSR) to extract patient names, claim IDs, and statuses.
    Returns a list of dicts: {'patient': name, 'claim_id': id, 'status': status, 'line_content': line}
    """
    if not file_contents:
        return []
    
    extracted = []
    # Regex structure: TYPE(Word) ClaimID(Word) PatientName(Last, First) DOS(Date) Charge(Float) Payer(Word/Spaces)
    # Example: REAP    387268Z43267   SANCHEZ, LAZARO      03/10/2025     232.00  UNITEDHEALTHCARE
    # Regex note: Patient name can contain spaces and commas.
    pattern = re.compile(r'^\s*([A-Z]+)\s+([A-Z0-9]+)\s+([A-Z, ]+?)\s+(\d{2}/\d{2}/\d{4})\s+([\d.]+)\s+([A-Z0-9 ]+?)\s+', re.MULTILINE)
    
    for match in pattern.finditer(file_contents):
        extracted.append({
            'type': match.group(1),
            'claim_id': match.group(2),
            'patient': match.group(3).strip(),
            'dos': match.group(4),
            'charge': match.group(5),
            'payer': match.group(6).strip()
        })
    return extracted

def resolve_rejections(rejections, lookback_window_reports):
    """
    Filters out rejections if a later report indicates success (REJECTED=0) for the same patient/payer.
    """
    resolved_rejections = []
    unresolved_rejections = []
    
    # 1. Build Success Registry
    success_events = []
    
    print_debug("Building Success Event Registry...")
    for report in lookback_window_reports:
        # Check if CSR and Rejected == 0
        is_csr = report.get('FILENAME', '').endswith('.CSR')
        
        if is_csr:
            report_rejected_count = int(report.get('REJECTED', 0))
            if report_rejected_count == 0:
                claims_in_report = parse_csr_report(report.get('FILECONTENTS', ''))
                report_date = report.get('FILERECEIVEDATE')
                
                for c in claims_in_report:
                    success_events.append({
                        'patient': c['patient'],
                        'payer': c['payer'],
                        'date': report_date,
                        'file': report.get('FILENAME')
                    })
    
    print_debug(f"Found {len(success_events)} success events to cross-reference.")
    
    # 2. Check each rejection
    for rej in rejections:
        rejected_claims = parse_csr_report(rej.get('FILECONTENTS', ''))
        
        is_this_file_resolved = True 
        
        if not rejected_claims:
            print_debug(f"Could not parse claims in rejection file {rej['FILENAME']}. Keeping as unresolved.")
            unresolved_rejections.append(rej)
            continue
            
        for rc in rejected_claims:
            p_name = rc['patient']
            p_payer = rc['payer']
            rej_date = rej.get('FILERECEIVEDATE')
            
            # Look for success event
            found_resolution = False
            for event in success_events:
                same_patient = event['patient'] == p_name
                # Loose payer match? Just use patient for now if payer string varies slighty.
                # But safer to use both.
                # Assuming exact match for now based on 'UNITEDHEALTHCARE' consistency.
                same_payer = event['payer'] == p_payer
                later_date = event['date'] > rej_date
                
                if same_patient and same_payer and later_date:
                    found_resolution = True
                    print_debug(f"RESOLVED: Rejection for {p_name} ({rej['FILENAME']}) resolved by {event['file']} on {event['date']}")
                    break
            
            if not found_resolution:
                is_this_file_resolved = False
        
        if is_this_file_resolved:
            resolved_rejections.append(rej)
        else:
            unresolved_rejections.append(rej)

    print_debug(f"Resolution Summary: {len(resolved_rejections)} resolved, {len(unresolved_rejections)} still actively rejected.")
    return unresolved_rejections

def extract_eras_rejections():
    print_debug(f"Starting extraction for {TARGET_PRACTICE_NAME} ({TARGET_PRACTICE_GUID})...")
    print_debug(f"Lookback window: {LOOKBACK_HOURS} hours")
    
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Max Date
        print_debug("Checking max FILERECEIVEDATE...")
        date_query = f"""
        SELECT MAX(FILERECEIVEDATE) 
        FROM PM_CLEARINGHOUSERESPONSE 
        WHERE PRACTICEGUID = '{TARGET_PRACTICE_GUID}'
        """
        cursor.execute(date_query)
        max_date = cursor.fetchone()[0]
        print_debug(f"Max FILERECEIVEDATE: {max_date}")
        
        if not max_date:
            return []

        # 2. Fetch ALL Reports
        print_debug("Fetching ALL Clearinghouse Responses in window...")
        all_query = f"""
        SELECT 
            PRACTICEGUID, 
            CLEARINGHOUSERESPONSETYPENAME, 
            CLEARINGHOUSERESPONSEREPORTTYPENAME,
            ITEMCOUNT, 
            DENIED, 
            REJECTED, 
            TOTALAMOUNT, 
            FILENAME, 
            PAYMENTID, 
            RESPONSETYPE, 
            SOURCENAME, 
            TITLE, 
            FILERECEIVEDATE,
            FILECONTENTS
        FROM PM_CLEARINGHOUSERESPONSE
        WHERE PRACTICEGUID = '{TARGET_PRACTICE_GUID}'
          AND FILERECEIVEDATE >= DATEADD(hour, -{LOOKBACK_HOURS}, '{max_date}')
        ORDER BY FILERECEIVEDATE ASC
        """
        cursor.execute(all_query)
        columns = [col[0] for col in cursor.description]
        all_records = [dict(zip(columns, row)) for row in cursor.fetchall()]
        print_debug(f"Fetched {len(all_records)} total records.")
        
        # 3. Categorize
        eras = []
        raw_rejections = []
        
        for r in all_records:
            if r.get('CLEARINGHOUSERESPONSEREPORTTYPENAME') == 'ERA':
                eras.append(r)
                # Add parsed info for ERA
                r['PARSED_INFO'] = parse_835_snippet(r.get('FILECONTENTS', ''))
            
            if r.get('CLEARINGHOUSERESPONSEREPORTTYPENAME') == 'Processing' and r.get('REJECTED', 0) > 0:
                raw_rejections.append(r)

        print_debug(f"Identified {len(eras)} ERAs and {len(raw_rejections)} Potential Rejections.")
        
        # 4. Smart Resolve
        print_debug("Applying Smart Rejection Logic...")
        active_rejections = resolve_rejections(raw_rejections, all_records)
        
        final_output = eras + active_rejections
        
        # Output
        output_file = "eras_rejections_single_practice.json"
        with open(output_file, "w") as f:
            json.dump(final_output, f, default=str, indent=2)
        print_debug(f"Saved {len(final_output)} records to {output_file}")
        
        # Table
        display_data = []
        for r in final_output:
            d = r.copy()
            d.pop('FILECONTENTS', None)
            d['PARSED'] = 'Yes' if r in eras else 'Rejection'
            if 'PARSED_INFO' in d:
                 d['CLP_COUNT'] = d['PARSED_INFO'].get('clp_count', 0)
                 d.pop('PARSED_INFO', None)
            display_data.append(d)

        print_debug("Generating summary table (Filtered):")
        print_table(display_data, ["FILERECEIVEDATE", "CLEARINGHOUSERESPONSEREPORTTYPENAME", "FILENAME", "TOTALAMOUNT", "REJECTED", "CLP_COUNT"])

        return final_output

    except Exception as e:
        print_debug(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        cursor.close()
        conn.close()
        print_debug("Connection closed.")

if __name__ == "__main__":
    extract_eras_rejections()
