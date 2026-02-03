from src.connection import get_connection

def list_tables():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SHOW TABLES LIKE 'PM_%'")
        tables = [row[1] for row in cursor.fetchall()]
        print(tables)
    except Exception as e: print(e)

if __name__ == "__main__":
    list_tables()
