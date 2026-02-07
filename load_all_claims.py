"""
Script to load all service_lines.csv files from extraction output into fin_claim_line table.
"""
import psycopg2
import csv
import os
import hashlib
from glob import glob

DB_CONFIG = {
    "host": "localhost",
    "database": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password"
}

def generate_id(input_str):
    return hashlib.md5(input_str.encode()).hexdigest()

def clean_date(val):
    """Convert YYYYMMDD to YYYY-MM-DD"""
    if not val or val.strip() == '':
        return None
    val = str(val).strip()
    if len(val) == 8 and val.isdigit():
        return f"{val[:4]}-{val[4:6]}-{val[6:8]}"
    return val

def clean_money(val):
    if not val:
        return 0.0
    s = str(val).replace('$', '').replace(',', '').strip()
    if not s:
        return 0.0
    try:
        return float(s)
    except:
        return 0.0

def load_all_service_lines():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Find all service_lines.csv files
    csv_files = glob("output_all_practices/*/service_lines.csv")
    print(f"Found {len(csv_files)} service_lines.csv files")
    
    total_loaded = 0
    
    for csv_file in csv_files:
        practice_name = os.path.basename(os.path.dirname(csv_file))
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            batch = []
            
            for i, row in enumerate(reader):
                claim_ref = row.get('ClaimID', '')
                enc_ref = row.get('LineID_Ref6R', '')  # This is encounter ID reference
                
                # Try to map encounter_id
                encounter_id = None
                if enc_ref and enc_ref.isdigit():
                    encounter_id = int(enc_ref)
                
                # Generate unique ID
                unique_str = f"{claim_ref}_{row.get('Date')}_{row.get('ProcCode')}_{i}"
                tebra_id = generate_id(unique_str)
                
                # Parse proc code - remove HC: prefix if present
                proc_code = row.get('ProcCode', '')
                if proc_code.startswith('HC:'):
                    proc_code = proc_code.split(':')[1] if ':' in proc_code else proc_code
                
                # Parse date
                dos = clean_date(row.get('Date'))
                
                batch.append((
                    tebra_id,
                    encounter_id,
                    claim_ref,
                    proc_code,
                    dos,
                    clean_money(row.get('Billed')),
                    clean_money(row.get('Paid')),
                    int(float(row.get('Units') or 1)),
                    row.get('Adjustments'),
                    row.get('Status', '1')  # Default status
                ))
            
            if batch:
                try:
                    # Insert with upsert
                    from psycopg2.extras import execute_values
                    execute_values(
                        cur,
                        """
                        INSERT INTO tebra.fin_claim_line (
                            tebra_claim_id, encounter_id, claim_reference_id,
                            proc_code, date_of_service, billed_amount, paid_amount, units,
                            adjustments_json, claim_status
                        ) VALUES %s
                        ON CONFLICT (tebra_claim_id) DO UPDATE
                        SET paid_amount = EXCLUDED.paid_amount,
                            adjustments_json = EXCLUDED.adjustments_json
                        """,
                        batch,
                        page_size=500
                    )
                    conn.commit()
                    print(f"  {practice_name}: Loaded {len(batch)} lines")
                    total_loaded += len(batch)
                except Exception as e:
                    conn.rollback()
                    print(f"  {practice_name}: ERROR - {e}")
    
    print(f"\n=== TOTAL: Loaded {total_loaded} claim lines ===")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    load_all_service_lines()
