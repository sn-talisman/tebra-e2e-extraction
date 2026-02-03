from src.connection import get_connection

def inspect_claim():
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"\n--- PM_CLAIM ---")
    try:
        cursor.execute(f"DESCRIBE TABLE PM_CLAIM")
        for row in cursor.fetchall():
            print(f"{row[0]} ({row[1]})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_claim()
