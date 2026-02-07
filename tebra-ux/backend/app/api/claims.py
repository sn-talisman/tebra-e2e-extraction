from fastapi import APIRouter, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any

router = APIRouter()

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
    # Only capitalize if it looks like ALL CAPS or needs formatting
    if text.isupper():
        return " ".join(word.capitalize() for word in text.split())
    return text

@router.get("/{claim_ref_id}/details")
def get_claim_details(claim_ref_id: str):
    """
    Get detailed view for a specific claim reference ID
    aggregating all associated lines and payment info.
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
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
        
        if not lines:
            raise HTTPException(status_code=404, detail="Claim details not found")
            
        # 2. Fetch ERA Payments
        cur.execute("""
            SELECT 
                payer_name,
                total_paid,
                total_patient_resp,
                received_date
            FROM tebra.fin_era_bundle
            WHERE claim_reference_id = %s
        """, (claim_ref_id,))
        eras = cur.fetchall()

        # 3. Aggregate Header Info (from first line)
        first_line = lines[0]
        
        response = {
            "header": {
                "claimRefId": claim_ref_id,
                "date": str(first_line['date_of_service']),
                "patient": {
                    "name": first_line['patient_name'],
                    "id": first_line['patient_id']
                },
                "provider": first_line['provider_name'],
                "status": first_line['payer_status'] or first_line['claim_status'] or 'Pending'
            },
            "financials": {
                "lines": [
                    {
                        "date": str(l['date_of_service']),
                        "procCode": l['proc_code'],
                        "description": l['description'], # Keeping original case as requested
                        "billed": float(l['billed_amount'] or 0),
                        "paid": float(l['paid_amount'] or 0),
                        "units": l['units'],
                        "adjustments": l['adjustments_json'],
                        "adjustmentDescriptions": l['adjustment_descriptions']
                    } for l in lines
                ],
                "totals": {
                    "billed": sum(float(l['billed_amount'] or 0) for l in lines),
                    "paid": sum(float(l['paid_amount'] or 0) for l in lines),
                    "balance": sum(float(l['billed_amount'] or 0) - float(l['paid_amount'] or 0) for l in lines)
                },
                "eras": [
                    {
                        "payer": e['payer_name'],
                        "paid": float(e['total_paid'] or 0),
                        "patientResp": float(e['total_patient_resp'] or 0),
                        "checkNumber": "N/A", # Not available in schema
                        "checkDate": str(e['received_date']) if e['received_date'] else None
                    } for e in eras
                ]
            }
        }
        
        return response

    finally:
        cur.close()
        conn.close()
