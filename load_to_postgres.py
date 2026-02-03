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

def clean_id(val):
    if not val or val.strip() == '': return None
    return val.strip()

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

def load_practice_data(data_dir='.'):
    conn = get_db()
    if not conn: return
    
    # Files acting as our "Single Practice" source
    file_era = os.path.join(data_dir, 'claims_extracted.csv')
    file_enc = os.path.join(data_dir, 'encounters_enriched_deterministic.csv')
    
    if not os.path.exists(file_era) or not os.path.exists(file_enc):
        print(f"Source files not found in {data_dir}.")
        return

    print(f"Starting Load Transaction for {data_dir}...")
    try:
        cur = conn.cursor()
        
        # ==========================================================
        # 1. Load ERA Bundles (Parents)
        # ==========================================================
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
                    clean_money(row.get('PatResp'))
                    # ReceivedDate missing in this CSV, default to null or enrich later
                ))
                seen_bundles.add(ref_id)
        
        sql_bundle = """
            INSERT INTO tebra.fin_era_bundle (claim_reference_id, payer_name, total_paid, total_patient_resp)
            VALUES %s
            ON CONFLICT (claim_reference_id) DO UPDATE 
            SET total_paid = EXCLUDED.total_paid
        """
        execute_batch(cur, sql_bundle, bundles, "ERA Bundles")

        # ==========================================================
        # 2. Load Clinical & Entities
        # ==========================================================
        print("Phase 2: Clinical Data...")
        
        batch_pat = []
        batch_prov = []
        batch_loc = []
        batch_ins = []
        batch_enc = []
        batch_diag = []
        batch_line = []
        
        seen_pat = set()
        seen_prov = set()
        seen_loc = set()
        seen_ins = set()
        seen_enc = set()
        seen_line = set()
        
        with open(file_enc, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Entities
                pat_guid = row.get('DB_PatientGUID')
                if pat_guid and pat_guid not in seen_pat:
                    # Added Patient Mapping
                    batch_pat.append((
                        pat_guid, row.get('PatientID'), row.get('PatientName'), row.get('PatientCaseID'),
                        clean_date(row.get('PatientDOB')), row.get('PatientGender'),
                        row.get('PatientAddress'), row.get('PatientCity'), row.get('PatientState'), row.get('PatientZip')
                    )) 
                    seen_pat.add(pat_guid)
                
                prov_guid = row.get('ProviderGUID')
                if prov_guid and prov_guid not in seen_prov:
                    batch_prov.append((prov_guid, row.get('ProviderNPI'), row.get('ProviderName')))
                    seen_prov.add(prov_guid)
                    
                loc_guid = row.get('ServiceLocationGUID')
                if loc_guid and loc_guid not in seen_loc:
                    addr_json = json.dumps({
                        'address': row.get('FacilityAddress'), 
                        'city': row.get('FacilityCity'), 
                        'state': row.get('FacilityState')
                    })
                    batch_loc.append((loc_guid, row.get('FacilityName'), addr_json))
                    seen_loc.add(loc_guid)
                
                # Insurance
                pol_num = row.get('Insurance_PolicyNum')
                grp_num = row.get('Insurance_GroupNum')
                pol_key = None
                if pol_num or grp_num:
                    pol_key = make_policy_key(pol_num, grp_num)
                    if pol_key not in seen_ins:
                        batch_ins.append((
                            pol_key, row.get('Insurance_Company'), row.get('Insurance_Plan'), pol_num, grp_num,
                            clean_date(row.get('Policy_Start')), clean_date(row.get('Policy_End')), clean_money(row.get('Policy_Copay'))
                        ))
                        seen_ins.add(pol_key)
                
                # Encounter
                enc_id = row.get('EncounterID')
                if enc_id and enc_id not in seen_enc:
                    batch_enc.append((
                        enc_id, row.get('Enc_EncounterGUID'), clean_date(row.get('EncounterDate')),
                        row.get('EncounterStatus'), row.get('Appt_Type'), row.get('Appt_Reason') or row.get('Appt_Desc'),
                        row.get('Appt_Subject'), 
                        row.get('Appt_Notes'),   
                        row.get('POS_Desc'),
                        pat_guid, prov_guid, loc_guid, pol_key,
                        row.get('ReferringProvGUID')
                    ))
                    
                    # Diagnoses
                    for i in range(1, 9):
                        d_code = row.get(f'DiagID_{i}')
                        d_desc = row.get(f'DiagDesc_{i}')
                        if d_code:
                            batch_diag.append((enc_id, d_code, i, d_desc))
                            
                    seen_enc.add(enc_id)
                

# ... (omitted) ...

                # Claim Line
                line_id = clean_id(row.get('DB_ClaimID'))
                era_ref = row.get('ClaimID')
                enc_id = clean_id(row.get('EncounterID'))
                
                if line_id and line_id not in seen_line:
                    batch_line.append((
                        line_id, enc_id, era_ref,
                        row.get('ProcCode'), row.get('Proc_Description') or row.get('Proc_Name') or row.get('Proc_TypeDesc'),
                        clean_date(row.get('Date')),
                        clean_money(row.get('Billed')), clean_money(row.get('Paid')), 
                        int(float(row.get('Units') or 0)),
                        parse_adjustments(row.get('Adjustments')),
                        row.get('Adjustment_Descriptions'),
                        parse_modifiers(row),
                        row.get('Claim_Status'),
                        row.get('Payer_Status'),
                        row.get('CH_Payer'),
                        row.get('Tracking_Num')
                    ))
                    seen_line.add(line_id)

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
        
        # Schema Migration on File (Transient)
        try:
             cur.execute("ALTER TABLE tebra.fin_claim_line ADD COLUMN IF NOT EXISTS adjustment_descriptions TEXT")
             cur.execute("ALTER TABLE tebra.fin_claim_line ADD COLUMN IF NOT EXISTS modifiers_json JSONB")
             cur.execute("ALTER TABLE tebra.fin_claim_line ADD COLUMN IF NOT EXISTS claim_status TEXT")
             cur.execute("ALTER TABLE tebra.fin_claim_line ADD COLUMN IF NOT EXISTS payer_status TEXT")
             cur.execute("ALTER TABLE tebra.fin_claim_line ADD COLUMN IF NOT EXISTS clearinghouse_payer TEXT")
             cur.execute("ALTER TABLE tebra.fin_claim_line ADD COLUMN IF NOT EXISTS tracking_number TEXT")
             conn.commit()
        except Exception as e:
             conn.rollback() # Ignore if exists

        sql_line = """
            INSERT INTO tebra.fin_claim_line (
                tebra_claim_id, encounter_id, claim_reference_id,
                proc_code, description, date_of_service,
                billed_amount, paid_amount, units, adjustments_json, adjustment_descriptions, modifiers_json,
                claim_status, payer_status, clearinghouse_payer, tracking_number
            ) VALUES %s 
            ON CONFLICT (tebra_claim_id) DO UPDATE 
            SET description = EXCLUDED.description, 
                adjustment_descriptions = EXCLUDED.adjustment_descriptions, 
                modifiers_json = EXCLUDED.modifiers_json,
                claim_status = EXCLUDED.claim_status,
                payer_status = EXCLUDED.payer_status,
                tracking_number = EXCLUDED.tracking_number
        """
        execute_batch(cur, sql_line, batch_line, "Service Lines")
        
        conn.commit()
        print("Success! Transaction Committed.")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"CRITICAL FAILURE: Rolling back transaction. Error: {e}")
        conn.rollback()
        conn.close()

if __name__ == "__main__":
    load_practice_data()
