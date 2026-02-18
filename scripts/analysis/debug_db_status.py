import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "tebra-ux" / "backend"))

from app.db.connection import get_db_cursor

def check_counts():
    print("--- Checking DB Counts ---")
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT count(*) FROM tebra.fin_era_report")
            print(f"ERA Reports: {cur.fetchone()[0]}")
            
            cur.execute("SELECT count(*) FROM tebra.cmn_location")
            print(f"Locations: {cur.fetchone()[0]}")
            
            cur.execute("SELECT count(*) FROM tebra.fin_era_bundle")
            print(f"Bundles: {cur.fetchone()[0]}")

    except Exception as e:
        print(f"Error accessing Postgres: {e}")

if __name__ == "__main__":
    check_counts()
