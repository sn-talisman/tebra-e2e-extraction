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

def find_mixed_report():
    with get_db_cursor() as cur:
        # Find a report that has claim lines with 'Denied' status
        # and see what the header counts say
        cur.execute("""
            SELECT 
                r.era_report_id, 
                r.denied_count, 
                count(cl.tebra_claim_id) as actual_lines,
                count(case when cl.payer_status = 'Denied' OR cl.payer_status = 'Claim Rejected' then 1 end) as actual_denied
            FROM tebra.fin_era_report r
            JOIN tebra.fin_era_bundle b ON r.era_report_id = b.era_report_id
            JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
            GROUP BY r.era_report_id, r.denied_count
            HAVING count(case when cl.payer_status = 'Denied' OR cl.payer_status = 'Claim Rejected' then 1 end) > 0
            LIMIT 5
        """)
        
        rows = cur.fetchall()
        if rows:
            print("Found potential mixed reports:")
            for row in rows:
                print(f"ID: {row[0]} | Header Denied: {row[1]} | Actual Lines: {row[2]} | Actual Denied Items: {row[3]}")
                
            # Verify one closer
            target_id = rows[0][0]
            print(f"\nExample Claims for {target_id}:")
            cur.execute("""
                SELECT cl.tebra_claim_id, cl.payer_status, cl.billed_amount, cl.paid_amount
                FROM tebra.fin_era_bundle b
                JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
                WHERE b.era_report_id = %s
            """, (target_id,))
            claims = cur.fetchall()
            for c in claims:
                print(f" - Claim {c[0]}: Status='{c[1]}' Billed={c[2]} Paid={c[3]}")
                
        else:
            print("No reports found with Denied claim lines.")

if __name__ == "__main__":
    find_mixed_report()
