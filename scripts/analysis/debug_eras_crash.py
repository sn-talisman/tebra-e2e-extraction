import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "tebra-ux" / "backend"))
from app.db.connection import get_db_cursor

def reproduce_crash():
    practice_guid = '2e95cc85-2c11-6c6b-e063-98341e0ac8e2'
    page = 1
    page_size = 20
    offset = 0
    
    print("--- Reproducing Backend Query ---")
    
    sql = """
            SELECT 
                r.era_report_id,
                r.received_date,
                r.payer_name,
                r.check_number,
                -- Calculated Total Paid (Header is unreliable)
                COALESCE(
                    (SELECT SUM(cl.paid_amount) 
                     FROM tebra.fin_era_bundle b 
                     JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
                     WHERE b.era_report_id = r.era_report_id), 
                    r.total_paid, 
                    0
                ) as total_paid,
                r.payment_method,
                
                -- Practice Name
                COALESCE(loc.name, 'Unknown Practice') as practice_name,
                
                -- Source Metrics
                r.claim_count_source as claim_count,
                
                -- Calculated Status Counts
                COUNT(CASE 
                    WHEN cl.payer_status ILIKE '%%Denied%%' OR cl.claim_status ILIKE '%%Denied%%' THEN 1 
                    ELSE NULL 
                END) as denied_count,
                
                COUNT(CASE 
                    WHEN cl.payer_status ILIKE '%%Rejected%%' OR cl.claim_status ILIKE '%%Rejected%%' THEN 1 
                    ELSE NULL 
                END) as rejected_count,

                -- Denial Reasons (Aggregate Distinct Codes)
                STRING_AGG(DISTINCT cl.adjustments_json, ', ') FILTER (WHERE cl.paid_amount = 0) as denial_reasons,

                'Processed' as status_display
                
            FROM tebra.fin_era_report r
            LEFT JOIN tebra.cmn_location loc ON r.practice_guid::uuid = loc.location_guid
            LEFT JOIN tebra.fin_era_bundle b ON r.era_report_id = b.era_report_id
            LEFT JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
    """
    
    params = []
    where_clauses = []
    
    if practice_guid and practice_guid != 'All':
        where_clauses.append("r.practice_guid::uuid = %s")
        params.append(practice_guid)
        
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    sql += f"""
        GROUP BY r.era_report_id, r.received_date, r.payer_name, r.check_number, r.total_paid, r.payment_method, loc.name
    """

    sql += f" ORDER BY r.received_date DESC"
    
    sql += """
        LIMIT %s OFFSET %s
    """
    params.extend([page_size, offset])
    
    print("Executing SQL...")
    try:
        with get_db_cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            print(f"Success! Retrieved {len(rows)} rows.")
    except Exception as e:
        print(f"CRASHED: {e}")

if __name__ == "__main__":
    reproduce_crash()
