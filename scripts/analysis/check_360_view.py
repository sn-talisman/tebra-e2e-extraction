import psycopg2
import json

DB_CONFIG = {
    "dbname": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password",
    "host": "localhost",
    "port": "5432"
}

def verify_360(enc_id):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        query = """
        SELECT 
            -- 1. Demographics
            p.patient_id,
            doc.name as Provider,
            loc.name as Location,
            
            -- 2. Encounter/Clinical
            e.encounter_id,
            e.start_date,
            e.status,
            e.appt_reason,
            
            -- 3. Insurance
            ins.company_name,
            ins.policy_number,
            
            -- 4. Financial Bundle
            era.claim_reference_id,
            era.total_paid,
            
            -- 5. Line Details
            line.tebra_claim_id,
            line.proc_code,
            line.billed_amount,
            line.paid_amount,
            line.adjustments_json

        FROM tebra.clin_encounter e
        JOIN tebra.cmn_patient p ON e.patient_guid = p.patient_guid
        JOIN tebra.cmn_provider doc ON e.provider_guid = doc.provider_guid
        JOIN tebra.cmn_location loc ON e.location_guid = loc.location_guid
        LEFT JOIN tebra.ref_insurance_policy ins ON e.insurance_policy_key = ins.policy_key

        -- Link to Lines
        LEFT JOIN tebra.fin_claim_line line ON e.encounter_id = line.encounter_id

        -- Link to ERA Bundle
        LEFT JOIN tebra.fin_era_bundle era ON line.claim_reference_id = era.claim_reference_id

        WHERE e.encounter_id = %s
        ORDER BY line.tebra_claim_id;
        """
        
        cur.execute(query, (enc_id,))
        rows = cur.fetchall()
        
        print(f"\n--- 360 View for Encounter {enc_id} (Postgres) ---")
        if not rows:
            print("No records found.")
            return

        # Print Header Info (from first row)
        r0 = rows[0]
        print(f"Patient: {r0[0]} | Provider: {r0[1]}")
        print(f"Date: {r0[4]} | Status: {r0[5]} | Reason: {r0[6]}")
        print(f"Insurance: {r0[7]} (Pol: {r0[8]})")
        print("-" * 60)
        
        # Print Financials
        current_era = None
        for r in rows:
            era_ref = r[9]
            if era_ref != current_era:
                print(f"\n[ERA Bundle] Ref: {era_ref} | Check Total: ${r[10]}")
                current_era = era_ref
            
            adj = r[15]
            adj_str = json.dumps(adj) if adj else ""
            print(f"   Line {r[11]}: {r[12]} | Billed: ${r[13]} | Paid: ${r[14]} | Adj: {adj_str}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_360(388506)
