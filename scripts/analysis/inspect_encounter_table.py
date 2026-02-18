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

# Get sample data for type-related columns
cur.execute("SELECT encounter_id, appt_type, status, appt_reason FROM tebra.clin_encounter LIMIT 10")
rows = cur.fetchall()
print("\nSample Data:")
for row in rows:
    print(row)

conn.close()
