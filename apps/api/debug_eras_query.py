import os
import psycopg2
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

@contextmanager
def get_db_cursor():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "tebra_dw"),
        user=os.getenv("DB_USER", "tebra_user"),
        password=os.getenv("DB_PASSWORD", "tebra_password")
    )
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    finally:
        cur.close()
        conn.close()

def debug_query():
    print("Testing ERA List Query...")
    sql = """
        SELECT 
            r.era_report_id,
            r.received_date,
            r.payer_name,
            r.check_number,
            -- Calculated Total Paid
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
                WHEN cl.payer_status ILIKE '%Denied%' OR cl.claim_status ILIKE '%Denied%' THEN 1 
                ELSE NULL 
            END) as denied_count,
            
            COUNT(CASE 
                WHEN cl.payer_status ILIKE '%Rejected%' OR cl.claim_status ILIKE '%Rejected%' THEN 1 
                ELSE NULL 
            END) as rejected_count,

            -- Denial Reasons
            STRING_AGG(DISTINCT cl.adjustments_json, ', ') FILTER (WHERE cl.paid_amount = 0) as denial_reasons,

            'Processed' as status_display
            
        FROM tebra.fin_era_report r
        LEFT JOIN tebra.cmn_location loc ON r.practice_guid::uuid = loc.location_guid
        LEFT JOIN tebra.fin_era_bundle b ON r.era_report_id = b.era_report_id
        LEFT JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
        
        GROUP BY r.era_report_id, r.received_date, r.payer_name, r.check_number, r.total_paid, r.payment_method, loc.name
        LIMIT 5
    """
    
    try:
        with get_db_cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            print(f"Success! Fetched {len(rows)} rows.")
            for row in rows:
                print(row)
    except Exception as e:
        print(f"Query Failed: {e}")

if __name__ == "__main__":
    debug_query()
