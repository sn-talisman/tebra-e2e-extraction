import psycopg2
# DB Connection Config
DB_CONFIG = {
    "dbname": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password",
    "host": "localhost",
    "port": "5432"
}

def truncate_all():
    print("--- Truncating Tebra Data Warehouse Tables ---")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Order matters due to FKs, but CASCADE handles it.
        # We want to clear Financials AND the Clinical data linked to them to ensure no orphans.
        tables = [
            "tebra.fin_claim_line",
            "tebra.fin_era_bundle",
            "tebra.fin_era_report",
            "tebra.clin_encounter_diagnosis",
            "tebra.clin_encounter",
            "tebra.cmn_patient", 
            "tebra.cmn_provider",
            "tebra.cmn_location",
            "tebra.ref_insurance_policy"
        ]
        
        for t in tables:
            print(f"Truncating {t}...")
            cur.execute(f"TRUNCATE TABLE {t} CASCADE;")
        
        conn.commit()
        print("Success! All tables truncated.")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error truncating tables: {e}")

if __name__ == "__main__":
    truncate_all()
