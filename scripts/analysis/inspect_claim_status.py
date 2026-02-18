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

print("\n--- Distinct Claim Statuses ---")
try:
    cur.execute("SELECT DISTINCT claim_status, payer_status FROM tebra.fin_claim_line LIMIT 50")
    rows = cur.fetchall()
    for row in rows:
        print(row)
except Exception as e:
    print(e)

conn.close()
