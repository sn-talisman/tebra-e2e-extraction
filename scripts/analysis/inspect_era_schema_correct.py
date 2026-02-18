import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "tebra-ux" / "backend"))
from app.db.connection import get_db_cursor

def inspect_schema():
    print("--- Inspecting Schemas ---")
    with get_db_cursor() as cur:
        # Bundle Columns
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'tebra' AND table_name = 'fin_era_bundle'
        """)
        print("\ntebra.fin_era_bundle columns:")
        for row in cur.fetchall():
            print(f"- {row[0]}")
            
        # Claim Line Columns
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'tebra' AND table_name = 'fin_claim_line'
        """)
        print("\ntebra.fin_claim_line columns:")
        for row in cur.fetchall():
            print(f"- {row[0]}")

if __name__ == "__main__":
    inspect_schema()
