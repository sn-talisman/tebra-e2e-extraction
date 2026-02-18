import psycopg2
# DB Connection Config
DB_CONFIG = {
    "dbname": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password",
    "host": "localhost",
    "port": "5432"
}

def check_era_db():
    print("--- Checking ERA 280508 in DB ---")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT era_report_id, denied_count, rejected_count, total_paid 
            FROM tebra.fin_era_report 
            WHERE era_report_id = '280508'
        """)
        row = cur.fetchone()
        print(f"DB Row: {row}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_era_db()
