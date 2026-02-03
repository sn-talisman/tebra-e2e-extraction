from src.connection import get_connection

def list_tables():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SHOW TABLES LIKE 'PM_%'")
        rows = cur.fetchall()
        print("--- TABLES ---")
        for r in rows:
            print(r[1]) # Table Name
    finally:
        conn.close()

if __name__ == "__main__":
    list_tables()
