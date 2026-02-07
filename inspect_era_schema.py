import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": "localhost",
    "database": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password"
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

print("\n--- Columns in tebra.fin_era_bundle ---")
try:
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'tebra' AND table_name = 'fin_era_bundle'
    """)
    rows = cur.fetchall()
    for row in rows:
        print(row[0])
except Exception as e:
    print(e)

conn.close()
