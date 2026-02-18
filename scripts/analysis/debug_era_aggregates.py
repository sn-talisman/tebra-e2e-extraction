import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'tebra-ux/backend'))

from app.db.connection import get_db_cursor

def debug_aggregates():
    with get_db_cursor() as cur:
        # Find an ERA with explicit denials but issues
        # Or just pick the one from before 280508
        report_id = '280508' 
        
        print(f"Debugging Report: {report_id}")
        
        # 1. Check Header & Source Count
        cur.execute("SELECT total_paid, claim_count_source FROM tebra.fin_era_report WHERE era_report_id = %s", (report_id,))
        head = cur.fetchone()
        print(f"Header -> Total Paid: {head[0]}, Source Claims: {head[1]}")
        
        # 2. Check Lines Sums
        query = """
            SELECT 
                COUNT(cl.tebra_claim_id) as actual_lines,
                SUM(cl.billed_amount) as sum_billed,
                SUM(cl.paid_amount) as sum_paid,
                SUM(CASE 
                    WHEN (cl.payer_status ILIKE '%%Denied%%' OR cl.claim_status ILIKE '%%Denied%%')
                      OR (cl.billed_amount > 0 AND cl.paid_amount = 0)
                    THEN 1 
                    ELSE 0 
                END) as calc_denials
            FROM tebra.fin_era_bundle b
            JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
            WHERE b.era_report_id = %s
        """
        cur.execute(query, (report_id,))
        agg = cur.fetchone()
        print(f"Aggregates -> Lines: {agg[0]}, Sum Billed: {agg[1]}, Sum Paid: {agg[2]}, Calc Denials: {agg[3]}")
        
        # 3. Dump first few lines
        cur.execute("""
            SELECT cl.billed_amount, cl.paid_amount 
            FROM tebra.fin_era_bundle b
            JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
            WHERE b.era_report_id = %s
            LIMIT 5
        """, (report_id,))
        rows = cur.fetchall()
        print("Sample Lines (Billed, Paid):")
        for r in rows:
            print(f"  {r[0]}, {r[1]}")

if __name__ == "__main__":
    debug_aggregates()
