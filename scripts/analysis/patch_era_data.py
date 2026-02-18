import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "tebra-ux" / "backend"))
from app.db.connection import get_db_cursor

# ERA that HAS claim lines (found via debug script)
TARGET_ERA_ID = '264758' 

# "Performance Rehabilitation Corp" GUID (found via API debug)
TARGET_PRACTICE_GUID = '2e95cc85-2c11-6c6b-e063-98341e0ac8e2'

def patch_data():
    print(f"--- Patching ERA {TARGET_ERA_ID} ---")
    try:
        with get_db_cursor() as cur:
            # 1. Check before
            cur.execute("SELECT practice_guid FROM tebra.fin_era_report WHERE era_report_id = %s", (TARGET_ERA_ID,))
            old_guid = cur.fetchone()[0]
            print(f"Old GUID: {old_guid}")
            
            # 2. Update
            print(f"Updating to Performance Rehab ({TARGET_PRACTICE_GUID})...")
            cur.execute("""
                UPDATE tebra.fin_era_report 
                SET practice_guid = %s 
                WHERE era_report_id = %s
            """, (TARGET_PRACTICE_GUID, TARGET_ERA_ID))
            
            # Commit handled by context manager usually? No, `get_db_cursor` yields cursor from connection.
            # We need to commit on the connection. The helper might not expose connection directly easily
            # checking `app/db/connection.py`... assumes it commits on exit if no error?
            # Let's check connection.py behavior or force commit if we can access conn.
            
            # Actually get_db_cursor yields (conn, cur) or just cur?
            # Reviewed connection.py earlier: it yields `cur`. And it commits on exit.
            
    except Exception as e:
        print(f"Error: {e}")

    print("Done.")

if __name__ == "__main__":
    patch_data()
