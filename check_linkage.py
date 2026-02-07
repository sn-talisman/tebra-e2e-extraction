import psycopg2
# DB Connection Config
DB_CONFIG = {
    "dbname": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password",
    "host": "localhost",
    "port": "5432"
}

def check_linkage():
    print("--- Checking Practice Linkage ---")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        guid = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'
        
        # 1. Check cmn_practice
        cur.execute("SELECT name FROM tebra.cmn_practice WHERE practice_guid = %s", (guid,))
        row = cur.fetchone()
        print(f"cmn_practice: {row}")
        
        # 2. Check cmn_location (what eras.py joins on)
        cur.execute("SELECT name FROM tebra.cmn_location WHERE location_guid = %s", (guid,))
        row = cur.fetchone()
        print(f"cmn_location: {row}")
        
        # 3. Check fin_era_report sample
        cur.execute("SELECT practice_guid FROM tebra.fin_era_report WHERE era_report_id = '280508'")
        row = cur.fetchone()
        print(f"fin_era_report GUID: {row}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_linkage()
