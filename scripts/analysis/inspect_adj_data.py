import psycopg2
from psycopg2.extras import RealDictCursor
import json

DB_CONFIG = {
    "host": "localhost",
    "database": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password"
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=RealDictCursor)

print("\n--- Adjustment Data Sample ---")
cur.execute("""
    SELECT adjustments_json, adjustment_descriptions 
    FROM tebra.fin_claim_line 
    WHERE adjustments_json IS NOT NULL 
    LIMIT 1
""")
row = cur.fetchone()

if row:
    print("Adjustments JSON:", row['adjustments_json'])
    print("Descriptions:", row['adjustment_descriptions'])
    print("Descriptions Type:", type(row['adjustment_descriptions']))
else:
    print("No data with adjustments found")

conn.close()
