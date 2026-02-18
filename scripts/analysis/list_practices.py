from src.connection import get_connection

def list_practices():
    conn = get_connection()
    cursor = conn.cursor()
    
    print("Listing Practices...")
    try:
        # Guessing table name based on conventions
        cursor.execute("SELECT PRACTICEGUID, PRACTICENAME FROM PM_PRACTICE ORDER BY PRACTICENAME")
        practices = cursor.fetchall()
        print(f"Found {len(practices)} Practices:")
        for p in practices:
            print(f"- {p[1]} ({p[0]})")
            
    except Exception as e:
        print(f"Error: {e}")
        # Fallback inspection if PM_PRACTICE doesn't exist
        try:
            cursor.execute("SHOW TABLES LIKE 'PM_%PRACTICE%'")
            print("Tables found:", cursor.fetchall())
        except:
            pass
            
    conn.close()

if __name__ == "__main__":
    list_practices()
