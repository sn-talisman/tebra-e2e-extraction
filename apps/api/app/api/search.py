from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from app.db.connection import get_db_connection
import psycopg2.extras

router = APIRouter()

class SearchResult(BaseModel):
    type: str  # 'practice', 'patient', 'claim', 'status'
    id: str    # Unique ID for the item (GUID, claim_id, etc.)
    label: str # Display text
    subtext: Optional[str] = None # Additional info (e.g., Practice Name for a patient)
    metadata: Optional[dict] = {} # Extra data for navigation (practice_guid, tab, etc.)

@router.get("/", response_model=List[SearchResult])
async def search_global(
    q: str = Query(..., min_length=2, description="Search query"),
    type: Optional[str] = Query(None, description="Filter by type: practice, patient, claim, status")
):
    """
    Global search across Practices, Patients, Claims, and Statuses.
    """
    results = []
    q_str = f"%{q.lower()}%"
    
    try:
        # DB Search (Practices, Patients, Claims)
        if not type or type in ['practice', 'patient', 'claim']:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    if not type or type == 'practice':
                        cursor.execute("""
                            SELECT 
                                p.practice_guid, 
                                p.name, 
                                COALESCE(l.address_block->>'city', 'N/A') as city, 
                                COALESCE(l.address_block->>'state', 'N/A') as state
                            FROM tebra.cmn_practice p
                            LEFT JOIN tebra.cmn_location l ON p.name = l.name
                            WHERE LOWER(p.name) LIKE %s 
                               OR LOWER(l.address_block->>'city') LIKE %s
                            LIMIT 5
                        """, (q_str, q_str))
                        
                        for row in cursor.fetchall():
                            results.append(SearchResult(
                                type='practice',
                                id=str(row['practice_guid']),
                                label=row['name'],
                                subtext=f"{row['city']}, {row['state']}",
                                metadata={'practice_guid': str(row['practice_guid'])}
                            ))

                    # 2. Search Patients
                    if not type or type == 'patient':
                        # Link patient -> encounter -> location -> practice
                        # Select distinct to avoid duplicates from multiple encounters
                        cursor.execute("""
                            SELECT DISTINCT
                                p.patient_guid, 
                                p.full_name, 
                                p.patient_id, 
                                prac.practice_guid, 
                                prac.name as practice_name
                            FROM tebra.cmn_patient p
                            JOIN tebra.clin_encounter e ON p.patient_guid = e.patient_guid
                            JOIN tebra.cmn_location l ON e.location_guid = l.location_guid
                            JOIN tebra.cmn_practice prac ON l.name = prac.name
                            WHERE LOWER(p.full_name) LIKE %s 
                               OR LOWER(p.patient_id) LIKE %s
                            LIMIT 5
                        """, (q_str, q_str))
                        
                        for row in cursor.fetchall():
                            results.append(SearchResult(
                                type='patient',
                                id=str(row['patient_guid']),
                                label=row['full_name'],
                                subtext=f"ID: {row['patient_id']} • {row['practice_name']}",
                                metadata={
                                    'practice_guid': str(row['practice_guid']),
                                    'patient_guid': str(row['patient_guid']),
                                    'tab': 'patients'
                                }
                            ))

                    # 3. Search Claims
                    if not type or type == 'claim':
                        # Link claim (practice_guid is location_guid) -> location -> practice
                        cursor.execute("""
                            SELECT 
                                cl.tebra_claim_id, 
                                cl.claim_reference_id, 
                                cl.practice_guid as location_guid,
                                prac.practice_guid, 
                                prac.name as practice_name
                            FROM tebra.fin_claim_line cl
                            JOIN tebra.cmn_location l ON cl.practice_guid = l.location_guid
                            JOIN tebra.cmn_practice prac ON l.name = prac.name
                            WHERE LOWER(cl.tebra_claim_id) LIKE %s 
                               OR LOWER(cl.claim_reference_id) LIKE %s
                            LIMIT 5
                        """, (q_str, q_str))
                        
                        for row in cursor.fetchall():
                            results.append(SearchResult(
                                type='claim',
                                id=str(row['tebra_claim_id']),
                                label=f"Claim #{row['tebra_claim_id']}",
                                subtext=f"{row['practice_name']}",
                                metadata={
                                    'practice_guid': str(row['practice_guid']),
                                    'claim_ref_id': str(row['claim_reference_id']),
                                    'tab': 'claims'
                                }
                            ))

        # 4. Search Status (Static Check - No DB needed)
        if not type or type == 'status':
            statuses = ['Rejected', 'Denied', 'Paid']
            for status in statuses:
                if q.lower() in status.lower():
                    results.append(SearchResult(
                        type='status',
                        id=status,
                        label=f"ERA Status: {status}",
                        subtext="View in Electronic Remittance",
                        metadata={'status_filter': status}
                    ))

    except Exception as e:
        print(f"Search error: {e}")
        # Return empty results on error instead of 500 to prevent UI crash
        # or re-raise if you want the UI to handle it. 
        # For search typeahead, unexpected errors usually mean handle gracefully.
        # But let's log it.
        raise HTTPException(status_code=500, detail=str(e))

    return results
