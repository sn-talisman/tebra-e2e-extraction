import psycopg2
from psycopg2.extras import RealDictCursor
import json

DB_CONFIG = {
    "host": "localhost",
    "database": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password"
}

def get_claim_details(claim_ref_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        print(f"Fetching details for: {claim_ref_id}")
        
        # 1. Fetch Claim Lines
        cur.execute("""
            SELECT 
                cl.tebra_claim_id,
                cl.date_of_service,
                cl.proc_code,
                cl.description,
                cl.billed_amount,
                cl.paid_amount,
                cl.units,
                cl.adjustments_json,
                cl.adjustment_descriptions,
                cl.claim_status,
                cl.payer_status,
                e.encounter_id,
                p.full_name as patient_name,
                p.patient_id,
                pr.name as provider_name
            FROM tebra.fin_claim_line cl
            LEFT JOIN tebra.clin_encounter e ON cl.encounter_id = e.encounter_id
            LEFT JOIN tebra.cmn_patient p ON e.patient_guid = p.patient_guid
            LEFT JOIN tebra.cmn_provider pr ON e.provider_guid = pr.provider_guid
            WHERE cl.claim_reference_id = %s
            ORDER BY cl.date_of_service ASC
        """, (claim_ref_id,))
        
        lines = cur.fetchall()
        print(f"Found {len(lines)} lines")
        
        if not lines:
            print("No lines found!")
            return

        # 2. Fetch ERA Payments
        cur.execute("""
            SELECT 
                payer_name,
                total_paid,
                total_patient_resp,
                check_number,
                check_date
            FROM tebra.fin_era_bundle
            WHERE claim_reference_id = %s
        """, (claim_ref_id,))
        eras = cur.fetchall()
        print(f"Found {len(eras)} ERAs")

        # 3. Aggregate Header Info (from first line)
        first_line = lines[0]
        
        # Simulate processing - this is where it might fail if keys are wrong
        header = {
            "claimRefId": claim_ref_id,
            "date": str(first_line['date_of_service']),
            "patient": {
                "name": first_line['patient_name'],
                "id": first_line['patient_id']
            },
            "provider": first_line['provider_name'],
            "status": first_line['payer_status'] or first_line['claim_status'] or 'Pending'
        }
        print("Header constructed successfully")
        
    except Exception as e:
        print("\nERROR OCCURRED:")
        print(e)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    get_claim_details("378483Z43267")
