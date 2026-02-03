import psycopg2
import json

# Credentials
DB_CONFIG = {
    "dbname": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password",
    "host": "localhost",
    "port": "5432"
}

def find_candidate():
    print("Connecting to DB...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Query to find an encounter with:
    # 1. Patient info
    # 2. Insurance Info
    # 3. Claims/Lines attached
    # 4. ERA Bundle info attached (paid > 0)
    
    sql = """
    SELECT 
        e.encounter_id, 
        e.encounter_guid,
        p.case_id as patient_case_id,
        pro.npi as provider_npi,
        ins.company_name as payer,
        COUNT(l.tebra_claim_id) as line_count,
        SUM(l.billed_amount) as total_billed
    FROM tebra.clin_encounter e
    JOIN tebra.cmn_patient p ON e.patient_guid = p.patient_guid
    JOIN tebra.cmn_provider pro ON e.provider_guid = pro.provider_guid
    JOIN tebra.ref_insurance_policy ins ON e.insurance_policy_key = ins.policy_key
    JOIN tebra.fin_claim_line l ON e.encounter_id = l.encounter_id
    GROUP BY e.encounter_id, e.encounter_guid, p.case_id, pro.npi, ins.company_name
    HAVING COUNT(l.tebra_claim_id) > 1
    ORDER BY total_billed DESC
    LIMIT 5;
    """
    
    cur.execute(sql)
    rows = cur.fetchall()
    
    print("\n--- TOP 5 CANDIDATE ENCOUNTERS ---")
    for r in rows:
        print(f"EncID: {r[0]} | PatientCase: {r[2]} | Payer: {r[4]} | Lines: {r[5]} | Billed: ${r[6]}")

    conn.close()

if __name__ == "__main__":
    find_candidate()
