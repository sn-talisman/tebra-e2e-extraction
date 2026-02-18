import psycopg2


# DB Connection Config (Embedded for reliability)
DB_CONFIG = {
    "dbname": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password",
    "host": "localhost",
    "port": "5432"
}

def count_patients():
    print("--- Counting Unique Patients ---")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(DISTINCT patient_guid) FROM tebra.cmn_patient;")
        count = cur.fetchone()[0]
        
        print(f"Total Unique Patients: {count}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error counting patients: {e}")

if __name__ == "__main__":
    count_patients()
