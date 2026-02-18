from src.connection import get_connection

def find_multiclaim_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Logic:
    # 1. Encounter -> EncProc -> Claim
    # We want count(distinct ClaimID) > 1 for an EncounterID
    
    q = """
    SELECT 
        E.ENCOUNTERID,
        COUNT(DISTINCT C.CLAIMID) as ClaimCount
    FROM PM_CLAIM C
    JOIN PM_ENCOUNTERPROCEDURE EP ON C.ENCOUNTERPROCEDUREID = EP.ENCOUNTERPROCEDUREID
    JOIN PM_ENCOUNTER E ON EP.ENCOUNTERGUID = E.ENCOUNTERGUID
    GROUP BY E.ENCOUNTERID
    HAVING COUNT(DISTINCT C.CLAIMID) > 1
    ORDER BY ClaimCount DESC
    LIMIT 5
    """
    
    print("Searching for encounters with multiple claims...")
    try:
        cursor.execute(q)
        results = cursor.fetchall()
        for r in results:
            print(f"Encounter: {r[0]} | Claims: {r[1]}")
            
        if not results:
            print("No multi-claim encounters found in the linked set.")
            
    except Exception as e:
        print(e)
        
if __name__ == "__main__":
    find_multiclaim_db()
