import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any

DB_CONFIG = {
    "host": "localhost",
    "database": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def to_title_case(text):
    if not text:
        return ""
    return " ".join(word.capitalize() for word in text.split())

def get_encounter_details(encounter_id: int):
    print(f"Fetching details for encounter {encounter_id}")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. Context (Encounter & Location)
        print("Querying context...")
        cur.execute("""
            SELECT 
                e.encounter_guid,
                e.start_date,
                e.status,
                e.appt_type,
                e.appt_reason,
                e.pos_description,
                l.name as location_name,
                l.address_block
            FROM tebra.clin_encounter e
            JOIN tebra.cmn_location l ON e.location_guid = l.location_guid
            WHERE e.encounter_id = %s
        """, (encounter_id,))
        
        context = cur.fetchone()
        if not context:
            print("Encounter not found!")
            return
        
        # 2. Entities (Patient, Provider, Payer)
        print("Querying patient...")
        cur.execute("""
            SELECT 
                p.full_name as patient_name,
                p.patient_id,
                p.case_id,
                p.patient_guid,
                p.dob,
                p.address_line1,
                p.city,
                p.state,
                p.zip
            FROM tebra.clin_encounter e
            JOIN tebra.cmn_patient p ON e.patient_guid = p.patient_guid
            WHERE e.encounter_id = %s
        """, (encounter_id,))
        patient = cur.fetchone()
        
        print("Querying provider...")
        cur.execute("""
            SELECT 
                pr.name as provider_name,
                pr.npi
            FROM tebra.clin_encounter e
            LEFT JOIN tebra.cmn_provider pr ON e.provider_guid = pr.provider_guid
            WHERE e.encounter_id = %s
        """, (encounter_id,))
        provider = cur.fetchone()
        
        # 3. Clinical Data (Diagnoses)
        print("Querying diagnoses...")
        cur.execute("""
            SELECT diag_code, description, precedence
            FROM tebra.clin_encounter_diagnosis
            WHERE encounter_id = %s
            ORDER BY precedence ASC
        """, (encounter_id,))
        diagnoses = cur.fetchall()
        
        # 4. Financials (Claim Lines)
        print("Querying claim lines...")
        cur.execute("""
            SELECT 
                cl.date_of_service,
                cl.proc_code,
                cl.description,
                cl.billed_amount,
                cl.paid_amount,
                cl.units,
                cl.claim_reference_id,
                cl.adjustments_json
            FROM tebra.fin_claim_line cl
            WHERE cl.encounter_id = %s
            ORDER BY cl.date_of_service ASC
        """, (encounter_id,))
        lines = cur.fetchall()
        
        # 5. ERA Payment Bundles
        print("Querying ERAs...")
        era_bundles = []
        if lines:
            # unique claim ref ids
            claim_refs = list(set([l['claim_reference_id'] for l in lines if l['claim_reference_id']]))
            if claim_refs:
                placeholders = ', '.join(['%s'] * len(claim_refs))
                cur.execute(f"""
                    SELECT 
                        claim_reference_id,
                        payer_name,
                        total_paid as total_check_paid,
                        total_patient_resp
                    FROM tebra.fin_era_bundle
                    WHERE claim_reference_id IN ({placeholders})
                """, tuple(claim_refs))
                era_bundles = cur.fetchall()

        print("Formatting response...")
        response = {
            "context": {
                "encounterGuid": context['encounter_guid'],
                "date": str(context['start_date']),
                "status": context['status'],
                "type": context['appt_type'],
                "reason": context['appt_reason'],
                "placeOfService": context['pos_description'],
                "location": context['location_name'],
                "address": {
                    "city": to_title_case(context['address_block'].get('city', '')),
                    "state": context['address_block'].get('state', ''),
                    "line1": to_title_case(context['address_block'].get('address', '')) # address_block structure varies, assuming 'address' key
                } if context['address_block'] else None
            },
            "entities": {
                "patient": {
                    "name": patient['patient_name'],
                    "id": patient['patient_id'],
                    "guid": patient['patient_guid'],
                    "dob": str(patient['dob']),
                    "address": f"{to_title_case(patient['address_line1'])}, {to_title_case(patient['city'])}, {patient['state']} {patient['zip']}"
                } if patient else None,
                "provider": {
                    "name": provider['provider_name'],
                    "npi": provider['npi']
                } if provider else None,
                "payer": {
                    "name": era_bundles[0]['payer_name'] if era_bundles else "N/A" # Simplified
                }
            },
            "clinical": {
                "diagnoses": [
                    {
                        "code": d['diag_code'],
                        "description": d['description'],
                        "precedence": d['precedence']
                    } for d in diagnoses
                ]
            },
            "financials": {
                "lines": [
                    {
                        "date": str(l['date_of_service']),
                        "procCode": l['proc_code'],
                        "description": l['description'],
                        "billed": float(l['billed_amount'] or 0),
                        "paid": float(l['paid_amount'] or 0),
                        "units": l['units'],
                        "adjustments": l['adjustments_json']
                    } for l in lines
                ],
                "totals": {
                    "billed": sum(float(l['billed_amount'] or 0) for l in lines),
                    "paid": sum(float(l['paid_amount'] or 0) for l in lines)
                },
                "eraBundles": [
                    {
                        "claimRefId": e['claim_reference_id'],
                        "payer": e['payer_name'],
                        "paid": float(e['total_check_paid'] or 0),
                        "patientResp": float(e['total_patient_resp'] or 0)
                    } for e in era_bundles
                ]
            }
        }
        
        print("Success!")
        print(response)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    get_encounter_details(388496)
