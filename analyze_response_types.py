from src.connection import get_connection

# Practice: Performance Rehabilitation Corp
PRACTICE_GUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'

def analyze_types():
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"--- Analyzing Response Types for Practice {PRACTICE_GUID} ---")
    
    query = f"""
    SELECT CLEARINGHOUSERESPONSEREPORTTYPENAME, COUNT(*) as CNT
    FROM PM_CLEARINGHOUSERESPONSE 
    WHERE PRACTICEGUID = '{PRACTICE_GUID}'
    GROUP BY CLEARINGHOUSERESPONSEREPORTTYPENAME
    ORDER BY CNT DESC
    """
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"{'Report Type Name':<40} | {'Count':<10}")
        print("-" * 55)
        for name, count in rows:
            print(f"{name:<40} | {count:<10}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_types()
