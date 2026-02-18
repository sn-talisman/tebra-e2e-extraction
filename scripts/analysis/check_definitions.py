from src.connection import get_connection

def check_dict_tables():
    conn = get_connection()
    cur = conn.cursor()
    try:
        tables = ['PM_PROCEDURECODEDICTIONARY', 'PM_REMITTANCEREMARK', 'PM_HIPAAADJUSTMENT'] # Guessing on Adjustment
        
        # Check if tables exist first by listing slightly broader
        cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'PM_%PROCEDURE%' OR TABLE_NAME LIKE 'PM_%REMITTANCE%' OR TABLE_NAME LIKE 'PM_%ADJUSTMENT%'")
        rows = cur.fetchall()
        print("--- RELEVANT TABLES ---")
        found_tables = [r[0] for r in rows]
        for t in found_tables:
            print(t)
            
        print("\n--- COLUMNS ---")
        # Inspect promising ones
        targets = ['PM_PROCEDURECODEDICTIONARY', 'PM_REMITTANCEREMARK']
        for t in targets:
             if t in found_tables:
                cur.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{t}' ORDER BY ORDINAL_POSITION")
                cols = [r[0] for r in cur.fetchall()]
                print(f"{t}: {', '.join(cols)}")
                
    finally:
        conn.close()

if __name__ == "__main__":
    check_dict_tables()
