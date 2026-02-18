from src.connection import get_connection

def check_schema():
    conn = get_connection()
    cur = conn.cursor()
    try:
        tables = ['PM_DOCTOR', 'PM_PATIENT', 'PM_SERVICELOCATION']
        for t in tables:
            print(f"--- {t} ---")
            cur.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{t}' ORDER BY ORDINAL_POSITION")
            cols = [r[0] for r in cur.fetchall()]
            print(", ".join(cols))
    finally:
        conn.close()

if __name__ == "__main__":
    check_schema()
