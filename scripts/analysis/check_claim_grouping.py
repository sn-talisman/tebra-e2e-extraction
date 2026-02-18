import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": "localhost",
    "database": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password"
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=RealDictCursor)

print("\n--- Claim Grouping Check ---")
try:
    # Check if multiple lines share the same claim_reference_id
    cur.execute("""
        SELECT claim_reference_id, COUNT(*) as line_count 
        FROM tebra.fin_claim_line 
        WHERE claim_reference_id IS NOT NULL 
        GROUP BY claim_reference_id 
        HAVING COUNT(*) > 1 
        LIMIT 5
    """)
    rows = cur.fetchall()
    print("Multi-line claims found:", len(rows) > 0)
    for row in rows:
        print(row)
        
    # Check if tebra_claim_id is unique per line (PK)
    cur.execute("""
        SELECT tebra_claim_id, COUNT(*) 
        FROM tebra.fin_claim_line 
        GROUP BY tebra_claim_id 
        HAVING COUNT(*) > 1 
        LIMIT 1
    """)
    dupes = cur.fetchall()
    print("Duplicate tebra_claim_id found:", len(dupes) > 0)
    
except Exception as e:
    print(e)

conn.close()
