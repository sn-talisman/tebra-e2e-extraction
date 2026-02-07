import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "tebra-ux" / "backend"))
from app.db.connection import get_db_cursor

def check_linkage():
    print("--- Checking ERA -> Practice Linkage ---")
    with get_db_cursor() as cur:
        # Check simple join count
        query = """
            SELECT count(*)
            FROM tebra.fin_era_report r
            JOIN tebra.cmn_location loc ON r.practice_guid::uuid = loc.location_guid
        """
        cur.execute(query)
        print(f"ERAs matching a Practice: {cur.fetchone()[0]}")
        
        # Check sample un-matched
        q2 = """
            SELECT r.era_report_id, r.practice_guid, loc.name
            FROM tebra.fin_era_report r
            LEFT JOIN tebra.cmn_location loc ON r.practice_guid::uuid = loc.location_guid
            WHERE loc.location_guid IS NULL
            LIMIT 5
        """
        cur.execute(q2)
        print("\n--- Sample Unmatched ERAs ---")
        for row in cur.fetchall():
            print(f"ID: {row[0]}, P_GUID: {row[1]}")

        # Check sample matched
        q3 = """
            SELECT r.era_report_id, r.practice_guid, loc.name
            FROM tebra.fin_era_report r
            JOIN tebra.cmn_location loc ON r.practice_guid::uuid = loc.location_guid
            LIMIT 5
        """
        cur.execute(q3)
        print("\n--- Sample Matched ERAs ---")
        for row in cur.fetchall():
             print(f"ID: {row[0]}, Practice: {row[2]}")

if __name__ == "__main__":
    check_linkage()
