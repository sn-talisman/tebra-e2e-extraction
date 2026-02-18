from src.connection import get_connection

def check_adj():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PM_ADJUSTMENTREASON' ORDER BY ORDINAL_POSITION")
        cols = [r[0] for r in cur.fetchall()]
        print("--- PM_ADJUSTMENTREASON ---")
        print(", ".join(cols))
    finally:
        conn.close()

if __name__ == "__main__":
    check_adj()
