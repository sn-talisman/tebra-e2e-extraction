import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'tebra-ux/backend'))

from app.db.connection import get_db_cursor

def analyze_zero_pay_eras():
    with get_db_cursor() as cur:
        # Get sample of ERAs with 0 total paid
        query = """
            SELECT 
                r.era_report_id, 
                r.total_paid, 
                r.payment_method, 
                r.claim_count_source,
                COUNT(cl.tebra_claim_id) as claim_line_count,
                SUM(CASE WHEN cl.payer_status ILIKE '%%Denied%%' OR cl.claim_status ILIKE '%%Denied%%' THEN 1 ELSE 0 END) as explicit_denials
            FROM tebra.fin_era_report r
            LEFT JOIN tebra.fin_era_bundle b ON r.era_report_id = b.era_report_id
            LEFT JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
            WHERE r.total_paid = 0
            GROUP BY r.era_report_id, r.total_paid, r.payment_method, r.claim_count_source
            HAVING SUM(CASE WHEN (cl.payer_status ILIKE '%%Denied%%' OR cl.claim_status ILIKE '%%Denied%%') OR (cl.billed_amount > 0 AND cl.paid_amount = 0) THEN 1 ELSE 0 END) > 0
            LIMIT 20;
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        print(f"{'ID':<10} {'Paid':<10} {'Method':<10} {'Claims':<10} {'Lines':<10} {'Denials':<10}")
        print("-" * 80)
        for row in rows:
            print(f"{row[0]:<10} {row[1]:<10} {row[2]:<10} {row[3]:<10} {row[4]:<10} {row[5]:<10}")

if __name__ == "__main__":
    analyze_zero_pay_eras()
