import os
import psycopg2
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

@contextmanager
def get_db_cursor():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "tebra_dw"),
        user=os.getenv("DB_USER", "tebra_user"),
        password=os.getenv("DB_PASSWORD", "tebra_password")
    )
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    finally:
        cur.close()
        conn.close()

def patch_data():
    target_practice_guid = '2e95cc85-2c11-6c6b-e063-98341e0ac8e2' # PERF REHAB
    
    with get_db_cursor() as cur:
        # Find 50 arbitrary ERA reports
        # We use a subquery to select IDs to avoid updating ALL lines if we just missed a WHERE
        cur.execute("""
            UPDATE tebra.fin_era_report 
            SET practice_guid = %s
            WHERE era_report_id IN (
                SELECT era_report_id FROM tebra.fin_era_report LIMIT 50
            )
        """, (target_practice_guid,))
        
        row_count = cur.rowcount
        print(f"Updated {row_count} ERA reports to use practice {target_practice_guid}")

if __name__ == "__main__":
    patch_data()
