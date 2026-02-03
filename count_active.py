from src.connection import get_connection

def count_active():
    conn = get_connection()
    cursor = conn.cursor()
    print("Checking Active Practices...")
    try:
        # All
        cursor.execute("SELECT COUNT(*) FROM PM_PRACTICE")
        print(f"Total Practices: {cursor.fetchone()[0]}")
        
        # Active
        cursor.execute("SELECT COUNT(*) FROM PM_PRACTICE WHERE ACTIVE = TRUE")
        print(f"Active Practices: {cursor.fetchone()[0]}")
        
    except Exception as e:
        print(f"Error: {e}")
    conn.close()

if __name__ == "__main__":
    count_active()
