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

print("\n--- tebra.clin_encounter_diagnosis ---")
cur.execute("SELECT * FROM tebra.clin_encounter_diagnosis LIMIT 1")
if cur.description:
    print("Columns:", [col.name for col in cur.description])
else:
    print("No columns found or empty table")

conn.close()
