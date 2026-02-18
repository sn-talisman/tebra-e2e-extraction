from src.connection import get_connection

def investigate():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Find GUIDs (plural)
    name_pattern = 'BEHAVIORAL INTERVENTION%'
    cursor.execute(f"SELECT PRACTICEGUID, NAME FROM PM_PRACTICE WHERE NAME LIKE '{name_pattern}'")
    practices = cursor.fetchall()
    
    for guid, name in practices:
        print(f"\nTarget: {name} ({guid})")
        
        # 2. Query ALL responses (14 days back to be safe)
        query = f"""
        SELECT FILERECEIVEDATE, CLEARINGHOUSERESPONSEREPORTTYPENAME, FILENAME
        FROM PM_CLEARINGHOUSERESPONSE 
        WHERE PRACTICEGUID = '{guid}'
          AND FILERECEIVEDATE >= '2026-01-20'
        ORDER BY FILERECEIVEDATE DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"  Found {len(rows)} files since 2026-01-20:")
        for r in rows:
            print(f"  [{r[0]}] Type: {r[1]} | File: {r[2]}")

if __name__ == "__main__":
    investigate()
