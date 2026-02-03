from src.connection import get_connection

def check_diag_tables():
    conn = get_connection()
    cur = conn.cursor()
    try:
        tables = ['PM_ICD10DIAGNOSISCODEDICTIONARY', 'PM_DIAGNOSISCODEDICTIONARY']
        for t in tables:
            print(f"--- {t} ---")
            try:
                cur.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{t}' ORDER BY ORDINAL_POSITION")
                cols = [r[0] for r in cur.fetchall()]
                print(", ".join(cols))
            except Exception as e:
                print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_diag_tables()
