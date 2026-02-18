import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "tebra-ux" / "backend"))
from app.db.connection import get_db_cursor

ERA_ID = '264758'

def check_practice():
    print(f"--- Checking Practice for ERA {ERA_ID} ---")
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT r.era_report_id, r.practice_guid, loc.name
            FROM tebra.fin_era_report r
            LEFT JOIN tebra.cmn_location loc ON r.practice_guid::uuid = loc.location_guid
            WHERE r.era_report_id = %s
        """, (ERA_ID,))
        row = cur.fetchone()
        if row:
            print(f"Report ID: {row[0]}")
            print(f"Practice GUID: {row[1]}")
            print(f"Practice Name: {row[2]}")
        else:
            print("Report not found.")

if __name__ == "__main__":
    check_practice()
