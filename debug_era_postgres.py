import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "tebra-ux" / "backend"))

from app.db.connection import get_db_cursor

def check_postgres_data():
    print("--- Checking Postgres (tebra_dw) Data ---")
    try:
        with get_db_cursor() as cur:
            # 1. Check if the claim exists
            cur.execute("SELECT * FROM tebra.fin_claim_line WHERE tebra_claim_id = '601535'")
            row = cur.fetchone()
            if row:
                print("PASSED: Claim 601535 found in fin_claim_line.")
                print(f"Status: Payer='{row[6]}', Claim='{row[5]}'") # Adjust indices if needed, or dict
                print(f"Billed: {row[3]}, Paid: {row[4]}")
            else:
                print("FAILED: Claim 601535 NOT found in fin_claim_line.")

            # 2. Check Status Values
            print("\n--- Distinct Payer Statuses ---")
            cur.execute("SELECT DISTINCT payer_status FROM tebra.fin_claim_line LIMIT 10")
            rows = cur.fetchall()
            for r in rows:
                print(f"'{r[0]}'")

            print("\n--- Distinct Claim Statuses ---")
            cur.execute("SELECT DISTINCT claim_status FROM tebra.fin_claim_line LIMIT 10")
            rows = cur.fetchall()
            for r in rows:
                print(f"'{r[0]}'")

    except Exception as e:
        print(f"Error accessing Postgres: {e}")

if __name__ == "__main__":
    check_postgres_data()
