import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": "localhost",
    "database": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password"
}

def inspect_table(cur, table_name):
    print(f"\n--- {table_name} ---")
    cur.execute(f"SELECT * FROM {table_name} LIMIT 1")
    if cur.description:
        print("Columns:", [col.name for col in cur.description])
    else:
        print("No columns found or empty table")

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=RealDictCursor)

tables = [
    "tebra.cmn_patient",
    "tebra.cmn_provider",
    "tebra.clin_diagnosis",
    "tebra.fin_claim_line",
    "tebra.fin_era_bundle",
    "tebra.cmn_location"
]

for table in tables:
    inspect_table(cur, table)

conn.close()
