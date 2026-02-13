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

@router.get("/list")
def get_all_claims(
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    sort_by: str = 'date', # date, patient, practice, status, amount
    order: str = 'desc'
):
    """
    Get paginated list of all claims across all practices
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        offset = (page - 1) * page_size
        
        # Base Query
        # Grouping by Claim Reference ID to roll up lines into a single "Claim" for the list view
        # Using MAX/SUM for aggregates
        sql = """
            SELECT 
                cl.claim_reference_id as claim_id,
                MAX(cl.date_of_service) as date,
                MAX(p.full_name) as patient_name,
                MAX(pr.name) as practice_name,
                SUM(cl.billed_amount) as total_billed,
                SUM(cl.paid_amount) as total_paid,
                
                -- Determine Status priority: Paid > Rejected > Denied > Pending
                CASE 
                    WHEN SUM(cl.paid_amount) > 0 THEN 'Paid'
                    WHEN MAX(cl.payer_status) ILIKE '%%Rejected%%' OR MAX(cl.claim_status) ILIKE '%%Rejected%%' THEN 'Rejected'
                    WHEN MAX(cl.payer_status) ILIKE '%%Denied%%' OR MAX(cl.claim_status) ILIKE '%%Denied%%' THEN 'Denied'
                    ELSE COALESCE(MAX(cl.payer_status), MAX(cl.claim_status), 'Pending')
                END as status
                
            FROM tebra.fin_claim_line cl
            LEFT JOIN tebra.cmn_patient p ON cl.patient_guid = p.patient_guid
            LEFT JOIN tebra.cmn_practice pr ON cl.practice_guid = pr.practice_guid
        """
        
        params = []
        where_clauses = []
        
        if search:
            search_pattern = f"%{search}%"
            where_clauses.append("""
                (cl.claim_reference_id ILIKE %s OR 
                 p.full_name ILIKE %s OR 
                 pr.name ILIKE %s OR
                 cl.payer_status ILIKE %s)
            """)
            params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
            
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
            
        sql += " GROUP BY cl.claim_reference_id "
        
        # Sorting
        sort_map = {
            'date': 'MAX(cl.date_of_service)',
            'patient': 'MAX(p.full_name)',
            'practice': 'MAX(pr.name)',
            'amount': 'SUM(cl.billed_amount)',
            'status': '7' # Sort by the calculated column index (Postgres specific shorthand, or repeat expression)
        }
        
        # Careful with calculated column sorting in GROUP BY
        # Repeating the expression is safer
        if sort_by == 'status':
            order_expr = """
                CASE 
                    WHEN SUM(cl.paid_amount) > 0 THEN 'Paid'
                    WHEN MAX(cl.payer_status) ILIKE '%%Rejected%%' OR MAX(cl.claim_status) ILIKE '%%Rejected%%' THEN 'Rejected'
                    WHEN MAX(cl.payer_status) ILIKE '%%Denied%%' OR MAX(cl.claim_status) ILIKE '%%Denied%%' THEN 'Denied'
                    ELSE COALESCE(MAX(cl.payer_status), MAX(cl.claim_status), 'Pending')
                END
            """
        else:
            order_expr = sort_map.get(sort_by, 'MAX(cl.date_of_service)')
            
        direction = "DESC" if order == 'desc' else "ASC"
        
        sql += f" ORDER BY {order_expr} {direction}"
        
        # Pagination
        sql += " LIMIT %s OFFSET %s"
        params.extend([page_size, offset])
        
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        
        # Format response
        result = []
        for row in rows:
            result.append({
                "claimId": row['claim_id'],
                "date": str(row['date']),
                "patientName": row['patient_name'] or "Unknown",
                "practiceName": row['practice_name'] or "Unknown",
                "billed": float(row['total_billed'] or 0),
                "paid": float(row['total_paid'] or 0),
                "status": row['status']
            })
            
        return result

    except Exception as e:
        print(f"Error fetching claims list: {e}")
        return []
    finally:
        cur.close()
        conn.close()
