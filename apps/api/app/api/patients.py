from fastapi import APIRouter
from app.db.connection import get_db_cursor

router = APIRouter()

@router.get("/{patient_guid}/details")
async def get_patient_details(patient_guid: str):
    """Get comprehensive patient details including demographics, insurance, and encounters"""
    with get_db_cursor() as cur:
        # Patient demographics
        cur.execute("""
            SELECT 
                patient_guid,
                patient_id,
                full_name,
                case_id,
                dob,
                gender,
                address_line1,
                city,
                state,
                zip
            FROM tebra.cmn_patient
            WHERE patient_guid = %s
        """, (patient_guid,))
        
        patient_row = cur.fetchone()
        if not patient_row:
            return {"error": "Patient not found"}
        
        patient_data = {
            "patientGuid": str(patient_row[0]),
            "patientId": patient_row[1],
            "fullName": patient_row[2],
            "caseId": patient_row[3],
            "dob": str(patient_row[4]) if patient_row[4] else None,
            "gender": patient_row[5],
            "addressLine1": patient_row[6],
            "city": patient_row[7],
            "state": patient_row[8],
            "zip": patient_row[9]
        }
        
        # Insurance information (from most recent encounter)
        cur.execute("""
            SELECT 
                ip.company_name,
                ip.plan_name,
                ip.policy_number,
                ip.group_number
            FROM tebra.clin_encounter e
            LEFT JOIN tebra.ref_insurance_policy ip ON e.insurance_policy_key = ip.policy_key
            WHERE e.patient_guid = %s
            AND ip.company_name IS NOT NULL
            ORDER BY e.start_date DESC
            LIMIT 1
        """, (patient_guid,))
        
        insurance_row = cur.fetchone()
        insurance_data = None
        if insurance_row:
            insurance_data = {
                "companyName": insurance_row[0],
                "planName": insurance_row[1],
                "policyNumber": insurance_row[2],
                "groupNumber": insurance_row[3] or "N/A"
            }
        
        # Encounter history with financials
        cur.execute("""
            SELECT 
                e.encounter_id,
                e.start_date,
                e.status,
                COALESCE(l.name, 'Unknown Location') as location_name,
                COALESCE(SUM(cl.billed_amount), 0) as total_billed,
                COALESCE(SUM(cl.paid_amount), 0) as total_paid
            FROM tebra.clin_encounter e
            LEFT JOIN tebra.cmn_location l ON e.location_guid = l.location_guid
            LEFT JOIN tebra.fin_claim_line cl ON e.encounter_id = cl.encounter_id
            WHERE e.patient_guid = %s
            GROUP BY e.encounter_id, e.start_date, e.status, l.name
            ORDER BY e.start_date DESC
            LIMIT 50
        """, (patient_guid,))
        
        encounters = []
        for row in cur.fetchall():
            encounter_id = row[0]
            
            # Fetch diagnoses for this encounter
            cur.execute("""
                SELECT diag_code, description, precedence
                FROM tebra.clin_encounter_diagnosis
                WHERE encounter_id = %s
                ORDER BY precedence
            """, (encounter_id,))
            
            diagnoses = []
            for diag_row in cur.fetchall():
                diagnoses.append({
                    "code": diag_row[0],
                    "description": diag_row[1] or "No description available",
                    "precedence": diag_row[2]
                })
            
            encounters.append({
                "encounterId": encounter_id,
                "date": str(row[1]) if row[1] else "N/A",
                "status": row[2] or "N/A",
                "location": row[3],
                "diagnoses": diagnoses,
                "totalBilled": float(row[4] or 0),
                "totalPaid": float(row[5] or 0)
            })
        
        return {
            "patient": patient_data,
            "insurance": insurance_data,
            "encounters": encounters
        }
