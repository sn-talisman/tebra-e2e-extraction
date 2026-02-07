import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'tebra-ux/backend'))

from app.db.connection import get_db_cursor

def inspect_lines(report_id):
    with get_db_cursor() as cur:
        query = """
            SELECT 
                cl.tebra_claim_id,
                cl.proc_code,
                cl.billed_amount,
                cl.paid_amount,
                cl.claim_status,
                cl.payer_status,
                cl.adjustment_descriptions
            FROM tebra.fin_era_report r
            JOIN tebra.fin_era_bundle b ON r.era_report_id = b.era_report_id
            JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
            WHERE r.era_report_id = %s
        """
        cur.execute(query, (report_id,))
        rows = cur.fetchall()
        
        print(f"Lines for Report {report_id}:")
        print(f"{'ID':<10} {'Proc':<10} {'Billed':<10} {'Paid':<10} {'Status':<15} {'PayerStatus':<15}")
        print("-" * 80)
        for row in rows:
            print(f"{row[0]:<10} {row[1]:<10} {row[2]:<10} {row[3]:<10} {row[4]:<15} {row[5]:<15}")

        # Debug specific line
        print("\nDebugging Logic for 539331903332002:")
        cur.execute("""
            SELECT 
                billed_amount, 
                paid_amount, 
                (billed_amount > 0) as is_billed_pos,
                (paid_amount = 0) as is_paid_zero,
                (billed_amount > 0 AND paid_amount = 0) as combined_logic,
                pg_typeof(billed_amount) as billed_type,
                pg_typeof(paid_amount) as paid_type
            FROM tebra.fin_claim_line 
            WHERE tebra_claim_id = '539331903332002'
        """)
        drow = cur.fetchone()
        if drow:
            print(f"Billed: {drow[0]} ({drow[5]}), Paid: {drow[1]} ({drow[6]})")
            print(f"Billed > 0: {drow[2]}")
            print(f"Paid = 0: {drow[3]}")
            print(f"Combined: {drow[4]}")

if __name__ == "__main__":
    inspect_lines('253399')
