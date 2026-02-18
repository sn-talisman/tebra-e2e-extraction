import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "tebra-ux" / "backend"))
from app.db.connection import get_db_cursor

ERA_ID = '280269'  # The ID we know belongs to Performance Rehab

def debug_details():
    print(f"--- Debugging Data for ERA {ERA_ID} ---")
    with get_db_cursor() as cur:
        # 1. Check Report
        cur.execute("SELECT * FROM tebra.fin_era_report WHERE era_report_id = %s", (ERA_ID,))
        report = cur.fetchone()
        print(f"Report Exists: {bool(report)}")
        
        # 2. Check Bundles
        cur.execute("SELECT claim_reference_id, claim_reference_id, total_paid FROM tebra.fin_era_bundle WHERE era_report_id = %s", (ERA_ID,))
        bundles = cur.fetchall()
        print(f"Bundles Found: {len(bundles)}")
        
        for b in bundles:
            bid = b[0]
            ref_id = b[1]
            print(f"  Bundle {bid} (Ref: {ref_id})")
            
            # 3. Check Claim Lines for this Bundle
            # Using the same join logic as the backend
            cur.execute("SELECT count(*) FROM tebra.fin_claim_line WHERE claim_reference_id = %s", (ref_id,))
            count = cur.fetchone()[0]
            print(f"    -> Claim Lines: {count}")
            
            if count == 0:
                 # Check if the ref_id exists in claim line table AT ALL (maybe under different column?)
                 # cur.execute("SELECT count(*) FROM tebra.fin_claim_line WHERE claim_reference_id = %s", (ref_id,))
                 pass

    print("\n--- Global Check ---")
    with get_db_cursor() as cur:
        cur.execute("SELECT count(*) FROM tebra.fin_claim_line")
        total = cur.fetchone()[0]
        print(f"Total Claim Lines in DB: {total}")
        
        if total > 0:
            cur.execute("""
                SELECT b.era_report_id, count(cl.tebra_claim_id) as lines
                FROM tebra.fin_era_bundle b
                JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
                GROUP BY b.era_report_id
                LIMIT 1
            """)
            row = cur.fetchone()
            if row:
                print(f"Suggest testing ERA ID: {row[0]} (Has {row[1]} lines)")


if __name__ == "__main__":
    debug_details()
