from src.connection import get_connection

def inspect_claim_schema():
    conn = get_connection()
    cur = conn.cursor()
    
    print("--- PM_CLAIM SCHEMA ---")
    cur.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PM_CLAIM' ORDER BY ORDINAL_POSITION")
    cols = [r[0] for r in cur.fetchall()]
    for c in cols:
        print(c)
            
    conn.close()

if __name__ == "__main__":
    inspect_claim_schema()
