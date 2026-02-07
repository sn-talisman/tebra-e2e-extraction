import os
import sys
sys.path.append(os.path.join(os.getcwd(), 'tebra-ux/backend/app'))

# Mocking get_db_cursor/connection if needed, or importing if structure allows
# Assuming I can import get_db_connection from src or similar, but the API uses `backend.app.db` or similar
# Let's try to locate `get_db_cursor` definition first.
# It seems it was used in `eras.py`.
# I'll rely on finding it or just use psycopg2 directly for the debug script to avoid path issues, 
# but sharing the credentials logic is better.

# Let's look at eras.py imports to see where get_db_cursor comes from
from src.connection import get_connection
import psycopg2
from psycopg2.extras import DictCursor

def debug_query():
    conn = get_connection()
    cur = conn.cursor()
    
    practice_guid = None
    page = 1
    page_size = 20
    offset = (page - 1) * page_size
    
    sql = """
            SELECT 
                r.era_report_id,
                r.received_date,
                r.payer_name,
                r.check_number,
                r.total_paid,
                r.payment_method,
                
                -- Practice Name
                COALESCE(loc.name, 'Unknown Practice') as practice_name,
                
                -- Claim Count
                COUNT(DISTINCT b.claim_reference_id) as claim_count,
                
                -- Denied Count: Paid = 0 and Billed > 0
                COUNT(DISTINCT CASE WHEN cl.paid_amount = 0 AND cl.billed_amount > 0 THEN cl.tebra_claim_id END) as denied_count,
                
                -- Rejected Count: Status-based (e.g. 'Rejected', 'Failed', 'Error')
                -- Or if internal status indicates rejection.
                COUNT(DISTINCT CASE WHEN cl.claim_status IN ('Rejected', 'Failed', 'Error') THEN cl.tebra_claim_id END) as rejected_count,

                'Processed' as status_display
                
            FROM tebra.fin_era_report r
            LEFT JOIN tebra.cmn_location loc ON r.practice_guid = loc.location_guid
            LEFT JOIN tebra.fin_era_bundle b ON r.era_report_id = b.era_report_id
            LEFT JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
    """
    
    params = []
    where_clauses = []
    
    if practice_guid and practice_guid != 'All':
        where_clauses.append("r.practice_guid = %s")
        params.append(practice_guid)
        
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)
        
    sql += """
        GROUP BY r.era_report_id, r.received_date, r.payer_name, r.check_number, r.total_paid, r.payment_method, loc.name
        ORDER BY r.received_date DESC
        LIMIT %s OFFSET %s
    """
    params.extend([page_size, offset])
    
    print("Executing SQL...")
    try:
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        print(f"Success! Got {len(rows)} rows.")
        for row in rows[:2]:
            print(row)
    except Exception as e:
        print("SQL Execution Failed:")
        print(e)
    finally:
        conn.close()

if __name__ == "__main__":
    debug_query()
