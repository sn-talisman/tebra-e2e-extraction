from src.connection import get_connection

def list_tables_info():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'PM_%' ORDER BY TABLE_NAME")
        rows = cur.fetchall()
        print("--- TABLES FROM INFO SCHEMA ---")
        for r in rows:
            print(r[0])
    finally:
        conn.close()

if __name__ == "__main__":
    list_tables_info()
