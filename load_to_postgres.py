import csv
import psycopg2
import psycopg2.extras
import json
import os
import hashlib
from datetime import datetime

# Connection Config
DB_CONFIG = {
    "dbname": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password",
    "host": "localhost",
    "port": "5432"
}

BATCH_SIZE = 1000

def get_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Db Connect Error: {e}")
        return None

def clean_money(val):
    if not val: return 0.0
    s = str(val).replace('$','').replace(',','').strip()
    if not s: return 0.0
    try:
        return float(s)
    except:
        return 0.0

def clean_date(val):
    if not val or val.strip() == '': return None
    try:
        # standard ISO YYYY-MM-DD
        return val.strip()
    except:
        return None

def clean_int(val):
    if not val: return 0
    try:
        return int(float(str(val).strip()))
    except:
        return 0

def clean_id(val):
    if not val or val.strip() == '': return None
    return val.strip()

def clean_str(val):
    if not val: return None
    return str(val).replace('\x00', '').strip() or None

def parse_adjustments(adj_str):
    # Format: "CO-45:10.00; PR-3:5.00" -> JSON
    if not adj_str: return json.dumps({})
    result = {}
    parts = adj_str.split(';')
    for p in parts:
        if ':' in p:
            code, amt = p.strip().split(':', 1)
            result[code.strip()] = clean_money(amt)
    return json.dumps(result)

def parse_modifiers(row):
    mods = {}
    for i in range(1, 5):
        code = row.get(f'ModifierCode_{i}')
        if code:
            mods[code] = row.get(f'ModifierDesc_{i}', '')
    return json.dumps(mods) if mods else "{}"

def make_policy_key(pol, grp):
    raw = f"{pol or ''}|{grp or ''}"
    return hashlib.md5(raw.encode()).hexdigest()

def execute_batch(cursor, sql, data, desc):
    if not data: return
    try:
        psycopg2.extras.execute_values(cursor, sql, data, page_size=BATCH_SIZE)
        print(f"  -> {desc}: Loaded {len(data)} rows.")
    except Exception as e:
        print(f"  -> Error loading {desc}: {e}")
        raise e

def load_service_lines(conn):
    """
    Loads extracted service lines from service_lines.csv into tebra.fin_claim_line.
    Maps: ClaimID -> claim_reference_id
          LineID_Ref6R -> encounter_id (if numeric)
          Adjustments -> adjustments_json
    """
    cur = conn.cursor()
    data_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(data_dir, 'service_lines.csv')
    
    if not os.path.exists(file_path):
        print(f"Skipping service lines: {file_path} not found.")
        return

    print("Loading Service Lines...")
    batch_line = []
    
    # Simple integer ID generator if needed, but fin_claim_line PK is tebra_claim_id (bigint)
    # We can use a hash of ClaimID + Date + ProcCode + Index as ID if needed, 
    # OR let DB auto-increment if we change schema. But schema says 'not null' and no default?
    # Verify schema: `tebra_claim_id bigint not null`. No sequence default mentioned in my verify step?
    # Step 5761: `tebra_claim_id | bigint | not null |` (No 'default nextval...').
    # So I MUST provide an ID.
    # I'll generate a pseudo-random unique ID based on hash of row content to be deterministic.
    
    import hashlib
    def generate_id(s):
        return int(hashlib.md5(s.encode()).hexdigest(), 16) % (10**15)

    # Pre-fetch valid encounter IDs to avoid FK violations
    valid_enc_ids = set()
    try:
        cur.execute("SELECT encounter_id FROM tebra.clin_encounter")
        valid_enc_ids = {row[0] for row in cur.fetchall()}
    except Exception as e:
        print(f"Warning: Could not fetch encounters: {e}")

    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            claim_ref = row.get('ClaimID')
            enc_ref = row.get('LineID_Ref6R')
            
            # Try to map encounter ID
            encounter_id = None
            try:
                if enc_ref and enc_ref.isdigit():
                    eid = int(enc_ref)
                    if eid in valid_enc_ids:
                        encounter_id = eid
            except:
                pass
            
            # Generate unique ID for the line
            unique_str = f"{claim_ref}_{row.get('Date')}_{row.get('ProcCode')}_{i}"
            tebra_id = generate_id(unique_str)
            
            # Parse Adjustments to JSON
            adj_str = row.get('Adjustments')
            adj_json = json.dumps(adj_str) if adj_str else None

            # Date
            dos = clean_date(row.get('Date'))
            status = row.get('Status') or 'Processed'
            
            batch_line.append((
                tebra_id, encounter_id, claim_ref,
                row.get('ProcCode'), 
                dos,
                clean_money(row.get('Billed')), 
                clean_money(row.get('Paid')),
                clean_int(row.get('Units')),
                adj_json,
                status
            ))

    sql = """
        INSERT INTO tebra.fin_claim_line (
            tebra_claim_id, encounter_id, claim_reference_id, 
            proc_code, date_of_service, billed_amount, paid_amount, units,
            adjustments_json, claim_status
        )
        VALUES %s
        ON CONFLICT (tebra_claim_id) DO UPDATE 
        SET claim_reference_id = EXCLUDED.claim_reference_id,
            paid_amount = EXCLUDED.paid_amount,
            adjustments_json = EXCLUDED.adjustments_json,
            claim_status = EXCLUDED.claim_status
    """
    execute_batch(cur, sql, batch_line, "Service Lines")
    conn.commit()

def load_practice_info(cur, guid, name):
    if not guid: return
    sql = """
        INSERT INTO tebra.cmn_practice (practice_guid, name, active)
        VALUES (%s, %s, TRUE)
        ON CONFLICT (practice_guid) DO UPDATE
        SET name = EXCLUDED.name
    """
    try:
        cur.execute(sql, (guid, name))
    except Exception as e:
        print(f"Error loading practice info: {e}")

def load_practice_data(data_dir='.', practice_guid=None, practice_name=None, era_only=False):
    """Load practice data to Postgres.
    
    Args:
        data_dir: Directory containing the extracted CSV files
        era_only: If True, only load ERA reports (skip bundles and clinical data)
    """
    conn = get_db()
    if not conn: return
    
    # Files acting as our "Single Practice" source
    file_era = os.path.join(data_dir, 'claims_extracted.csv')
    file_enc = os.path.join(data_dir, 'encounters_enriched_deterministic.csv')
    file_reports = os.path.join(data_dir, 'era_reports.csv')
    
    # For ERA-only mode, we only need era_reports.csv
    if era_only:
        if not os.path.exists(file_reports):
            print(f"ERA reports file not found in {data_dir}.")
            return
    else:
        if not os.path.exists(file_era) or not os.path.exists(file_enc):
            print(f"Source files not found in {data_dir}.")
            return

    print(f"Starting Load Transaction for {data_dir}...{'  [ERA ONLY]' if era_only else ''}")
    try:
        cur = conn.cursor()
        
        # ==========================================================
        # Load Practice Info
        if practice_guid and practice_name:
            load_practice_info(cur, practice_guid, practice_name)
            conn.commit()
            
        print("Phase 0: ERA Reports...")

        
        if os.path.exists(file_reports):
            # Schema Migration for PracticeGUID (Transient)
            try:
                cur.execute("ALTER TABLE tebra.fin_era_report ADD COLUMN IF NOT EXISTS practice_guid TEXT")
                conn.commit()
            except Exception as e:
                conn.rollback()

            reports = []
            seen_reports = set()
            with open(file_reports, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rid = row.get('EraReportID')
                    if not rid or rid in seen_reports: continue
                    
                    reports.append((
                        rid, row.get('FileName'), clean_date(row.get('ReceivedDate')),
                        row.get('PayerName'), row.get('PayerID'),
                        row.get('CheckNumber'), clean_date(row.get('CheckDate')),
                        clean_money(row.get('TotalPaid')), row.get('Method'),
                        row.get('PracticeGUID'),
                        int(row.get('DeniedCount') or 0),
                        int(row.get('RejectedCount') or 0),
                        int(row.get('ClaimCount') or 0)
                    ))
                    seen_reports.add(rid)

            sql_report = """
                INSERT INTO tebra.fin_era_report (
                    era_report_id, file_name, received_date, payer_name, payer_id, 
                    check_number, check_date, total_paid, payment_method, practice_guid,
                    denied_count, rejected_count, claim_count_source
                ) VALUES %s
                ON CONFLICT (era_report_id) DO UPDATE
                SET total_paid = EXCLUDED.total_paid, 
                    check_number = EXCLUDED.check_number, 
                    practice_guid = EXCLUDED.practice_guid,
                    denied_count = EXCLUDED.denied_count,
                    rejected_count = EXCLUDED.rejected_count,
                    claim_count_source = EXCLUDED.claim_count_source
            """
            execute_batch(cur, sql_report, reports, "ERA Reports")

        # ==========================================================
        # 1. Load ERA Bundles (Parents) - Skip if ERA only
        # ==========================================================
        if not era_only and os.path.exists(file_era):
            print("Phase 1: ERA Bundles...")
            bundles = []
            seen_bundles = set()
            
            with open(file_era, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ref_id = row.get('ClaimID')
                    if not ref_id or ref_id in seen_bundles: continue
                    
                    bundles.append((
                        ref_id,
                        row.get('PayerName'),
                        clean_money(row.get('Paid')),
                        clean_money(row.get('PatResp')),
                        row.get('EraReportID') # New FK
                        # ReceivedDate missing in this CSV, default to null or enrich later
                    ))
                    seen_bundles.add(ref_id)
            
            sql_bundle = """
                INSERT INTO tebra.fin_era_bundle (claim_reference_id, payer_name, total_paid, total_patient_resp, era_report_id)
                VALUES %s
                ON CONFLICT (claim_reference_id) DO UPDATE 
                SET total_paid = EXCLUDED.total_paid, era_report_id = EXCLUDED.era_report_id
            """
            execute_batch(cur, sql_bundle, bundles, "ERA Bundles")
        elif era_only:
            print("Phase 1: Skipped (ERA Only Mode)")


        # ==========================================================
        # 2. Load Clinical & Entities - Skip if ERA only
        # ==========================================================
        if era_only:
            print("Phase 2: Skipped (ERA Only Mode)")
            conn.commit()
            print("Success! Transaction Committed.")
            cur.close()
            conn.close()
            return
            
        print("Phase 2: Clinical Data...")
        
        batch_pat = []
        batch_prov = []
        batch_loc = []
        batch_ins = []
        batch_enc = []
        batch_diag = []
        
        seen_pat = set()
        seen_prov = set()
        seen_loc = set()
        seen_ins = set()
        seen_enc = set()
        
        with open(file_enc, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Entities
                pat_guid = row.get('DB_PatientGUID')
                if pat_guid and pat_guid not in seen_pat:
                    # Added Patient Mapping
                    batch_pat.append((
                        pat_guid, clean_str(row.get('PatientID')), clean_str(row.get('PatientName')), clean_str(row.get('PatientCaseID')),
                        clean_date(row.get('PatientDOB')), clean_str(row.get('PatientGender')),
                        clean_str(row.get('PatientAddress')), clean_str(row.get('PatientCity')), clean_str(row.get('PatientState')), clean_str(row.get('PatientZip'))
                    )) 
                    seen_pat.add(pat_guid)
                
                prov_guid = row.get('ProviderGUID')
                if prov_guid and prov_guid not in seen_prov:
                    batch_prov.append((prov_guid, clean_str(row.get('ProviderNPI')), clean_str(row.get('ProviderName'))))
                    seen_prov.add(prov_guid)
                    
                loc_guid = row.get('ServiceLocationGUID')
                if loc_guid and loc_guid not in seen_loc:
                    addr_json = json.dumps({
                        'address': clean_str(row.get('FacilityAddress')), 
                        'city': clean_str(row.get('FacilityCity')), 
                        'state': clean_str(row.get('FacilityState'))
                    })
                    batch_loc.append((loc_guid, clean_str(row.get('FacilityName')), addr_json))
                    seen_loc.add(loc_guid)
                
                # Insurance
                pol_num = clean_str(row.get('Insurance_PolicyNum'))
                grp_num = clean_str(row.get('Insurance_GroupNum'))
                pol_key = None
                if pol_num or grp_num:
                    pol_key = make_policy_key(pol_num, grp_num)
                    if pol_key not in seen_ins:
                        batch_ins.append((
                            pol_key, clean_str(row.get('Insurance_Company')), clean_str(row.get('Insurance_Plan')), pol_num, grp_num,
                            clean_date(row.get('Policy_Start')), clean_date(row.get('Policy_End')), clean_money(row.get('Policy_Copay'))
                        ))
                        seen_ins.add(pol_key)
                
                # Encounter
                enc_id = row.get('EncounterID')
                if enc_id and enc_id not in seen_enc:
                    batch_enc.append((
                        enc_id, row.get('Enc_EncounterGUID'), clean_date(row.get('EncounterDate')),
                        clean_str(row.get('EncounterStatus')), clean_str(row.get('Appt_Type')), clean_str(row.get('Appt_Reason') or row.get('Appt_Desc')),
                        clean_str(row.get('Appt_Subject')), 
                        clean_str(row.get('Appt_Notes')),   
                        clean_str(row.get('POS_Desc')),
                        pat_guid, prov_guid, loc_guid, pol_key,
                        row.get('ReferringProvGUID')
                    ))
                    
                    # Diagnoses
                    enc_seen_diags = set()
                    for i in range(1, 9):
                        d_code = clean_str(row.get(f'DiagID_{i}'))
                        d_desc = clean_str(row.get(f'DiagDesc_{i}'))
                        if d_code and d_code not in enc_seen_diags:
                            batch_diag.append((enc_id, d_code, i, d_desc))
                            enc_seen_diags.add(d_code)
                            
                    seen_enc.add(enc_id)
                
                # End of Encounter processing
                # Old claim line logic removed - now handled by load_service_lines

        # Execute Batches
        # Schema Migrations (Transient)
        try:
             cur.execute("ALTER TABLE tebra.cmn_patient ADD COLUMN IF NOT EXISTS dob DATE")
             cur.execute("ALTER TABLE tebra.cmn_patient ADD COLUMN IF NOT EXISTS gender TEXT")
             cur.execute("ALTER TABLE tebra.cmn_patient ADD COLUMN IF NOT EXISTS address_line1 TEXT")
             cur.execute("ALTER TABLE tebra.cmn_patient ADD COLUMN IF NOT EXISTS city TEXT")
             cur.execute("ALTER TABLE tebra.cmn_patient ADD COLUMN IF NOT EXISTS state TEXT")
             cur.execute("ALTER TABLE tebra.cmn_patient ADD COLUMN IF NOT EXISTS zip TEXT")
             
             cur.execute("ALTER TABLE tebra.ref_insurance_policy ADD COLUMN IF NOT EXISTS start_date DATE")
             cur.execute("ALTER TABLE tebra.ref_insurance_policy ADD COLUMN IF NOT EXISTS end_date DATE")
             cur.execute("ALTER TABLE tebra.ref_insurance_policy ADD COLUMN IF NOT EXISTS copay NUMERIC(18,2)")
             
             cur.execute("ALTER TABLE tebra.clin_encounter ADD COLUMN IF NOT EXISTS referring_provider_guid TEXT")
             
             conn.commit()
        except Exception as e:
             conn.rollback()

        # Updated to UPSERT to backfill names
        sql_pat = """
            INSERT INTO tebra.cmn_patient (patient_guid, patient_id, full_name, case_id, dob, gender, address_line1, city, state, zip) 
            VALUES %s 
            ON CONFLICT (patient_guid) DO UPDATE 
            SET full_name = EXCLUDED.full_name, dob = EXCLUDED.dob, gender = EXCLUDED.gender, 
                address_line1 = EXCLUDED.address_line1, city = EXCLUDED.city, state = EXCLUDED.state, zip = EXCLUDED.zip
        """
        execute_batch(cur, sql_pat, batch_pat, "Patients")
        
        sql_prov = """
            INSERT INTO tebra.cmn_provider (provider_guid, npi, name) 
            VALUES %s 
            ON CONFLICT (provider_guid) DO UPDATE 
            SET npi = EXCLUDED.npi, name = EXCLUDED.name
        """
        execute_batch(cur, sql_prov, batch_prov, "Providers")
        
        sql_loc = """
            INSERT INTO tebra.cmn_location (location_guid, name, address_block) 
            VALUES %s 
            ON CONFLICT (location_guid) DO UPDATE 
            SET name = EXCLUDED.name, address_block = EXCLUDED.address_block
        """
        execute_batch(cur, sql_loc, batch_loc, "Locations")
        
        sql_ins = """
            INSERT INTO tebra.ref_insurance_policy (policy_key, company_name, plan_name, policy_number, group_number, start_date, end_date, copay) 
            VALUES %s 
            ON CONFLICT (policy_key) DO UPDATE
            SET start_date = EXCLUDED.start_date, end_date = EXCLUDED.end_date, copay = EXCLUDED.copay
        """
        execute_batch(cur, sql_ins, batch_ins, "Insurance Policies")
        
        # Schema Migration for Encounter (Transient)
        try:
             cur.execute("ALTER TABLE tebra.clin_encounter ADD COLUMN IF NOT EXISTS appt_subject TEXT")
             cur.execute("ALTER TABLE tebra.clin_encounter ADD COLUMN IF NOT EXISTS appt_notes TEXT")
             cur.execute("ALTER TABLE tebra.clin_encounter ADD COLUMN IF NOT EXISTS pos_description TEXT")
             conn.commit()
        except Exception as e:
             conn.rollback()

        sql_enc = """
            INSERT INTO tebra.clin_encounter (
                encounter_id, encounter_guid, start_date, status, appt_type, appt_reason,
                appt_subject, appt_notes, pos_description,
                patient_guid, provider_guid, location_guid, insurance_policy_key, referring_provider_guid
            ) VALUES %s 
            ON CONFLICT (encounter_id) DO UPDATE
            SET appt_subject = EXCLUDED.appt_subject, appt_notes = EXCLUDED.appt_notes, pos_description = EXCLUDED.pos_description, referring_provider_guid = EXCLUDED.referring_provider_guid
        """
        execute_batch(cur, sql_enc, batch_enc, "Encounters")
        
        # Schema Migration for Diag Description (Transient)
        try:
             cur.execute("ALTER TABLE tebra.clin_encounter_diagnosis ADD COLUMN IF NOT EXISTS description TEXT")
             conn.commit()
        except Exception as e:
             conn.rollback()

        sql_diag = """
            INSERT INTO tebra.clin_encounter_diagnosis (encounter_id, diag_code, precedence, description) 
            VALUES %s 
            ON CONFLICT (encounter_id, diag_code) DO UPDATE 
            SET description = EXCLUDED.description
        """
        execute_batch(cur, sql_diag, batch_diag, "Diagnoses")
        
        # ==========================================================
        # Phase 3: Load Claim Lines from Enriched CSV (with proper linkage)
        # ==========================================================
        print("Phase 3: Claim Lines (with Encounter Linkage)...")
        
        # ID generator for claim lines
        def generate_claim_id(s):
            return int(hashlib.md5(s.encode()).hexdigest(), 16) % (10**15)
        
        batch_claims = []
        seen_claims = set()
        
        with open(file_enc, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                enc_id = row.get('EncounterID')
                claim_ref = row.get('ClaimID')
                line_ref = row.get('LineID_Ref6R') or row.get('DB_ClaimID')
                loc_guid = row.get('ServiceLocationGUID')
                
                if not enc_id or not claim_ref:
                    continue
                
                # Generate unique ID for this claim line
                unique_str = f"{claim_ref}_{row.get('Date')}_{row.get('ProcCode')}_{line_ref}"
                if unique_str in seen_claims:
                    continue
                
                tebra_id = generate_claim_id(unique_str)
                
                # Parse adjustments to JSON format
                adj_str = row.get('Adjustments')
                adj_json = None
                if adj_str:
                    try:
                        adj_dict = parse_adjustments(adj_str)
                        adj_json = json.dumps(adj_dict) if adj_dict else None
                    except:
                        adj_json = json.dumps(adj_str)
                
                batch_claims.append((
                    tebra_id,
                    clean_int(enc_id),           # Proper encounter FK!
                    claim_ref,                    # Links to ERA bundle
                    row.get('ProcCode'),
                    row.get('Proc_Description'),
                    clean_date(row.get('Date')),
                    clean_money(row.get('Billed')),
                    clean_money(row.get('Paid')),
                    clean_int(row.get('Units')),
                    adj_json,
                    row.get('Adjustment_Descriptions'),
                    row.get('Claim_Status'),
                    row.get('Payer_Status'),
                    loc_guid,                     # Practice GUID
                    row.get('Tracking_Num'),
                    row.get('CH_Payer')
                ))
                seen_claims.add(unique_str)
        
        # Ensure practice_guid column exists
        try:
            cur.execute("ALTER TABLE tebra.fin_claim_line ADD COLUMN IF NOT EXISTS practice_guid UUID")
            cur.execute("ALTER TABLE tebra.fin_claim_line ADD COLUMN IF NOT EXISTS tracking_number TEXT")
            cur.execute("ALTER TABLE tebra.fin_claim_line ADD COLUMN IF NOT EXISTS clearinghouse_payer TEXT")
            conn.commit()
        except Exception as e:
            conn.rollback()
        
        sql_claim = """
            INSERT INTO tebra.fin_claim_line (
                tebra_claim_id, encounter_id, claim_reference_id,
                proc_code, description, date_of_service,
                billed_amount, paid_amount, units,
                adjustments_json, adjustment_descriptions,
                claim_status, payer_status, practice_guid,
                tracking_number, clearinghouse_payer
            ) VALUES %s
            ON CONFLICT (tebra_claim_id) DO UPDATE
            SET encounter_id = EXCLUDED.encounter_id,
                claim_reference_id = EXCLUDED.claim_reference_id,
                paid_amount = EXCLUDED.paid_amount,
                adjustments_json = EXCLUDED.adjustments_json,
                adjustment_descriptions = EXCLUDED.adjustment_descriptions,
                claim_status = EXCLUDED.claim_status,
                payer_status = EXCLUDED.payer_status
        """
        execute_batch(cur, sql_claim, batch_claims, "Claim Lines")
        print(f"    -> Loaded {len(batch_claims)} claim lines with encounter linkage.")
        
        conn.commit()
        print("Success! Transaction Committed.")
        
        # Phase 4: Consistency Check (User Request)
        # Ensure counts in fin_era_report match the actual claim lines
        print("Phase 4: Recalculating ERA Counts for Consistency...")
        try:
            cur.execute("""
                WITH counts AS (
                    SELECT 
                        b.era_report_id,
                        COUNT(CASE WHEN cl.payer_status ILIKE '%%Denied%%' OR cl.claim_status ILIKE '%%Denied%%' THEN 1 END) as d_count,
                        COUNT(CASE WHEN cl.payer_status ILIKE '%%Rejected%%' OR cl.claim_status ILIKE '%%Rejected%%' THEN 1 END) as r_count
                    FROM tebra.fin_era_bundle b
                    JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
                    GROUP BY b.era_report_id
                )
                UPDATE tebra.fin_era_report r
                SET denied_count = c.d_count,
                    rejected_count = c.r_count
                FROM counts c
                WHERE r.era_report_id = c.era_report_id
            """)
            conn.commit()
            print("    -> ERA Counts Updated from Line Items.")
        except Exception as e:
            print(f"    -> Warning: Could not update counts: {e}")
            conn.rollback()

        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"CRITICAL FAILURE: Rolling back transaction. Error: {e}")
        conn.rollback()
        conn.close()

if __name__ == "__main__":
    load_practice_data()
    # Also load newly extracted service lines
    conn = get_db()
    if conn:
        try:
            load_service_lines(conn)
        finally:
            conn.close()
