import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "tebra-ux" / "backend"))
from app.db.connection import get_db_cursor

def inspect_report_columns():
    print("--- Inspecting tebra.fin_era_report Columns ---")
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'tebra' AND table_name = 'fin_era_report'
        """)
        for row in cur.fetchall():
            print(f"- {row[0]} ({row[1]})")

if __name__ == "__main__":
    inspect_report_columns()
