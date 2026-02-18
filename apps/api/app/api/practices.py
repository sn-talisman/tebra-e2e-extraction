from fastapi import APIRouter
from app.db.connection import get_db_cursor

router = APIRouter()

@router.get("/")
async def get_practices_root():
    """Get list of all practice locations (root endpoint for frontend)"""
    return await get_practices()

@router.get("/list")
async def get_practices():
    with get_db_cursor() as cur:
        # STEP 1: Get all practices directly from the source of truth
        cur.execute("""
            SELECT 
                p.practice_guid, 
                p.name,
                COALESCE(MAX(l.address_block->>'city'), 'N/A') as city,
                COALESCE(MAX(l.address_block->>'state'), 'N/A') as state
            FROM tebra.cmn_practice p
            LEFT JOIN tebra.cmn_location l ON p.practice_guid = l.practice_guid
            GROUP BY p.practice_guid, p.name
        """)
        
        practices = {}
        for row in cur.fetchall():
            guid = str(row[0]).lower()
            practices[guid] = {
                "locationGuid": str(row[0]), # Frontend uses this as unique ID
                "name": row[1],
                "city": row[2],
                "state": row[3],
                "eraCount": 0,
                "encounterCount": 0
            }

        # STEP 2: Get ERA Counts (linked via practice_guid now)
        cur.execute("""
            SELECT 
                LOWER(practice_guid::text),
                COUNT(era_report_id)
            FROM tebra.fin_era_report
            GROUP BY practice_guid
        """)
        
        for row in cur.fetchall():
            guid, count = row
            if guid in practices:
                practices[guid]['eraCount'] = count

        # STEP 3: Get Encounter Counts (linked via practice_guid now)
        cur.execute("""
            SELECT 
                LOWER(practice_guid::text),
                COUNT(encounter_id)
            FROM tebra.clin_encounter
            GROUP BY practice_guid
        """)
        
        for row in cur.fetchall():
            guid, count = row
            if guid in practices:
                practices[guid]['encounterCount'] = count

        # Convert back to list and sort
        result_list = list(practices.values())
        # Sort by eraCount DESC, then name ASC
        result_list.sort(key=lambda x: (-x['eraCount'], x['name']))
        
        return result_list

@router.get("/{practice_guid}/patients")
async def get_practice_patients(practice_guid: str):
    """Get patients for a specific practice"""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT DISTINCT
                p.patient_guid,
                p.full_name,
                p.patient_id,
                COUNT(DISTINCT e.encounter_id) as encounter_count,
                MAX(e.start_date) as last_visit
            FROM tebra.cmn_patient p
            LEFT JOIN tebra.clin_encounter e ON p.patient_guid = e.patient_guid
            WHERE p.practice_guid = %s
            GROUP BY p.patient_guid, p.full_name, p.patient_id
            ORDER BY last_visit DESC NULLS LAST
            LIMIT 500
        """, (practice_guid,))
        
        rows = cur.fetchall()
        return [
            {
                "patientGuid": str(row[0]),
                "name": row[1],
                "patientId": row[2],
                "encounterCount": row[3],
                "lastVisit": str(row[4]) if row[4] else "N/A"
            }
            for row in rows
        ]

@router.get("/{practice_guid}/encounters")
async def get_practice_encounters(practice_guid: str):
    """Get encounters for a specific practice"""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                e.encounter_id,
                e.start_date,
                p.full_name as patient_name,
                pr.name as provider_name,
                e.appt_type,
                e.status
            FROM tebra.clin_encounter e
            INNER JOIN tebra.cmn_patient p ON e.patient_guid = p.patient_guid
            LEFT JOIN tebra.cmn_provider pr ON e.provider_guid = pr.provider_guid
            WHERE e.practice_guid = %s
            ORDER BY e.start_date DESC
            LIMIT 500
        """, (practice_guid,))
        
        rows = cur.fetchall()
        return [
            {
                "encounterId": row[0],
                "date": str(row[1]) if row[1] else "N/A",
                "patientName": row[2],
                "providerName": row[3] or "N/A",
                "type": row[4],
                "status": row[5] or "N/A"
            }
            for row in rows
        ]

@router.get("/{practice_guid}/claims")
async def get_practice_claims(practice_guid: str, paid_only: bool = False):
    """Get claims for a specific practice, optionally filtering by paid status"""
    with get_db_cursor() as cur:
        # Base query
        query = """
            SELECT 
                cl.tebra_claim_id,
                cl.date_of_service,
                COALESCE(p.full_name, 'Unknown') as patient_name,
                cl.billed_amount,
                cl.paid_amount,
                COALESCE(cl.claim_reference_id, '') as claim_reference_id,
                CASE 
                    WHEN cl.payer_status = 'Paid' THEN 'Paid'
                    WHEN cl.payer_status = 'Claim Rejected' THEN 'Rejected'
                    WHEN cl.payer_status = 'Claim Accepted' THEN 'Accepted'
                    WHEN cl.claim_status = 'Pending' THEN 'Pending'
                    WHEN cl.paid_amount > 0 THEN 'Paid'
                    ELSE 'Pending'
                END as status,
                cl.proc_code
            FROM tebra.fin_claim_line cl
            LEFT JOIN tebra.cmn_patient p ON cl.patient_guid = p.patient_guid
            WHERE cl.practice_guid = %s
        """
        
        params = [practice_guid]
        
        # Add filter if requested
        if paid_only:
            query += " AND cl.paid_amount > 0"
            
        # Add order and limit
        query += " ORDER BY cl.date_of_service DESC LIMIT 500"

        cur.execute(query, tuple(params))
        
        rows = cur.fetchall()
        return [
            {
                "claimId": row[0],
                "date": str(row[1]) if row[1] else "N/A",
                "patientName": row[2],
                "billed": float(row[3] or 0),
                "paid": float(row[4] or 0),
                "claimReferenceId": row[5],
                "status": row[6],
                "procCode": row[7]
            }
            for row in rows
        ]
