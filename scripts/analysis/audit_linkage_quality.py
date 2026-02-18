import logging
import json
import re
from src.connection import get_connection
from src.era_parser_xml import EraParser

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger('Audit')

# Practice to Audit (Perf Rehab)
PRACTICE_GUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'

def audit_linkage():
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"--- Auditing Data Linkage for Practice {PRACTICE_GUID} ---")
    
    # 1. Fetch recent ERAs
    print("1. Fetching recent ERAs from Snowflake...")
    cursor.execute(f"""
        SELECT TOP 5 FILENAME, FILECONTENTS, FILERECEIVEDATE 
        FROM PM_CLEARINGHOUSERESPONSE 
        WHERE PRACTICEGUID = '{PRACTICE_GUID}'
          AND CLEARINGHOUSERESPONSEREPORTTYPENAME = 'ERA'
        ORDER BY FILERECEIVEDATE DESC
    """)
    rows = cursor.fetchall()
    print(f"   -> Found {len(rows)} recent ERAs.")
    
    parser = EraParser()
    ref_ids = set()
    total_claims = 0
    
    # 2. Extract Reference IDs (Ref6R)
    print("\n2. Parsing ERAs for Reference IDs...")
    for row in rows:
        filename = row[0]
        content = row[1]
        try:
            parsed = parser.parse(content)
            claims = parsed.get('claims', [])
            total_claims += len(claims)
            
            for c in claims:
                # Check Header ClaimID
                if c.get('claim_id'):
                    ref_ids.add(c.get('claim_id'))
                
                # Check Service Line Refs
                for svc in c.get('service_lines', []):
                    for r in svc.get('refs', []):
                         if r['type'] == '6R':
                             val = r['value']
                             # Clean K prefix if present (logic from extract_batch)
                             match = re.search(r'K(\d{6})[A-Z0-9]*$', val)
                             if match: val = match.group(1)
                             ref_ids.add(val)
        except Exception as e:
            print(f"   [!] Failed to parse {filename}: {e}")

    print(f"   -> Extracted {len(ref_ids)} unique Reference IDs from {total_claims} claims.")
    
    # User Domain Rule: Numeric = Claim ID, Alphanumeric = Bundle/Ref ID
    numeric_ids = {rid for rid in ref_ids if rid.isdigit()}
    bundle_ids = ref_ids - numeric_ids
    
    print(f"   -> Identified {len(numeric_ids)} Claim IDs (Numeric) and {len(bundle_ids)} Bundle IDs (Alphanumeric).")
    
    if not numeric_ids:
        print("   [!] No valid numeric Claim IDs found. This ERA file might be purely Bundles or unstructured.")
        # Proceeding to check if bundles match is out of scope for this audit step
        return

    # 3. Verify Linkage to PM_CLAIM (Numeric Only)
    print("\n3. Verifying Linkage to PM_CLAIM (Numeric IDs only)...")
    ids_str = ", ".join([f"'{r}'" for r in numeric_ids])
    
    cursor.execute(f"""
        SELECT CLAIMID, ENCOUNTERPROCEDUREID, PATIENTGUID 
        FROM PM_CLAIM 
        WHERE CLAIMID IN ({ids_str})
    """)
    res_claims = cursor.fetchall()
    linked_claims = {str(r[0]) for r in res_claims}
    
    print(f"   -> Matched {len(linked_claims)} / {len(numeric_ids)} Numeric IDs in PM_CLAIM table.")
    if len(numeric_ids) > 0:
        print(f"   -> Match Rate: {len(linked_claims)/len(numeric_ids)*100:.1f}%")
    
    missing = list(numeric_ids - linked_claims)[:5]
    if missing:
        print(f"   -> Sample Missing IDs: {missing}")
        
    # 4. Verify Linkage to Encounters
    print("\n4. Verifying Linkage to Encounters...")
    enc_proc_ids = [r[1] for r in res_claims if r[1]]
    
    if enc_proc_ids:
        ep_ids_str = ", ".join([f"'{ep}'" for ep in enc_proc_ids])
        cursor.execute(f"""
            SELECT count(DISTINCT ENCOUNTERGUID) 
            FROM PM_ENCOUNTERPROCEDURE 
            WHERE ENCOUNTERPROCEDUREID IN ({ep_ids_str})
        """)
        enc_count = cursor.fetchone()[0]
        print(f"   -> Found {enc_count} distinct Encounters linked to these claims.")
    else:
        print("   -> No EncounterProcedure IDs found on matched claims.")

    print("\n--- Audit Complete ---")
    conn.close()

if __name__ == "__main__":
    audit_linkage()
