import psycopg2

DB_CONFIG = {
    "dbname": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password",
    "host": "localhost",
    "port": "5432"
}

def verify():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'tebra';
        """)
        
        tables = cur.fetchall()
        print(f"Found {len(tables)} tables in 'tebra' schema:")
        for t in tables:
            print(f"- {t[0]}.{t[1]}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
