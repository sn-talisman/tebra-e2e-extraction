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

cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'tebra'
""")

tables = cur.fetchall()
print("Tables in 'tebra' schema:")
for table in tables:
    print(table[0])

conn.close()
