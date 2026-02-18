from src.connection import get_connection

def inspect():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DESCRIBE TABLE PM_PRACTICE")
        for r in cursor.fetchall():
            print(f"{r[0]} ({r[1]})")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()

if __name__ == "__main__":
    inspect()
