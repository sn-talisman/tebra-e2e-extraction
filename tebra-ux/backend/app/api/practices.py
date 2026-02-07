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
        # We use a CTE to try two methods of linking practice to location:
        # 1. Via ERA -> Bundle -> Claim -> Location (most accurate but sparse)
        # 2. Via Name Match (fallback, covers ~40% of cases)
        cur.execute("""
            WITH PracticeMetadata AS (
                SELECT 
                    p.practice_guid,
                    p.name,
                    -- Prioritize ERA-linked location, fall back to name-matched location
                    COALESCE(l_era.address_block->>'city', l_name.address_block->>'city', 'N/A') as city,
                    COALESCE(l_era.address_block->>'state', l_name.address_block->>'state', 'N/A') as state,
                    -- Count ERAs directly linked to the practice
                    COUNT(DISTINCT r.era_report_id) as era_count,
                    -- Rank them to pick the best metadata if multiple locations found
                    ROW_NUMBER() OVER (PARTITION BY p.practice_guid ORDER BY COUNT(DISTINCT r.era_report_id) DESC) as rn
                FROM tebra.cmn_practice p
                
                -- Path 1: ERA Chain
                LEFT JOIN tebra.fin_era_report r ON p.practice_guid::text = LOWER(r.practice_guid)
                LEFT JOIN tebra.fin_era_bundle b ON r.era_report_id = b.era_report_id
                LEFT JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
                LEFT JOIN tebra.cmn_location l_era ON cl.practice_guid = l_era.location_guid
                
                -- Path 2: Name Match Fallback
                LEFT JOIN tebra.cmn_location l_name ON p.name = l_name.name
                
                GROUP BY p.practice_guid, p.name, l_era.address_block, l_name.address_block
            )
            SELECT 
                practice_guid,
                name,
                city,
                state,
                era_count
            FROM PracticeMetadata
            ORDER BY era_count DESC, name ASC
        """)
        
        rows = cur.fetchall()
        return [
            {
                "locationGuid": str(row[0]),
                "name": row[1],
                "city": row[2],
                "state": row[3],
                "eraCount": row[4]
            }
            for row in rows
        ]

@router.get("/{location_guid}/patients")
async def get_practice_patients(location_guid: str):
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
            INNER JOIN tebra.clin_encounter e ON p.patient_guid = e.patient_guid
            WHERE e.location_guid = %s
            GROUP BY p.patient_guid, p.full_name, p.patient_id
            ORDER BY last_visit DESC
        """, (location_guid,))
        
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

@router.get("/{location_guid}/encounters")
async def get_practice_encounters(location_guid: str):
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
            WHERE e.location_guid = %s
            ORDER BY e.start_date DESC
        """, (location_guid,))
        
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

@router.get("/{location_guid}/claims")
async def get_practice_claims(location_guid: str):
    """Get claims for a specific practice"""
    with get_db_cursor() as cur:
        cur.execute("""
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
            LEFT JOIN tebra.clin_encounter e ON cl.encounter_id = e.encounter_id
            LEFT JOIN tebra.cmn_patient p ON e.patient_guid = p.patient_guid
            WHERE cl.practice_guid = %s
            ORDER BY cl.date_of_service DESC
            LIMIT 500
        """, (location_guid,))
        
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
