from src.connection import get_connection

def check_cardinality():
    conn = get_connection()
    cur = conn.cursor()
    
    print("--- CARDINALITY CHECK ---")
    cur.execute("SELECT COUNT(*), COUNT(DISTINCT ENCOUNTERPROCEDUREID) FROM PM_CLAIM")
    row = cur.fetchone()
    print(f"Total Rows in PM_CLAIM: {row[0]}")
    print(f"Distinct EncounterProcIDs: {row[1]}")
    
    if row[0] > row[1]:
        print("Note: EncounterProcedureID is NOT unique. One procedure can have multiple claims (resubmissions?).")
        
        # Check an example
        cur.execute("""
            SELECT ENCOUNTERPROCEDUREID, COUNT(*) c 
            FROM PM_CLAIM 
            GROUP BY ENCOUNTERPROCEDUREID 
            HAVING c > 1 
            LIMIT 5
        """)
        dups = cur.fetchall()
        print("Examples of duplicates:")
        for d in dups:
            print(f"  EP_ID: {d[0]} -> {d[1]} Claims")
            
    conn.close()

if __name__ == "__main__":
    check_cardinality()
