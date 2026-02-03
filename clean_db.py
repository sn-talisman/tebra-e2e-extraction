from load_to_postgres import get_db

def clean_db():
    conn = get_db()
    if not conn: return
    
    cur = conn.cursor()
    tables = [
        'fin_claim_line',
        'fin_era_bundle',
        'clin_encounter_diagnosis',
        'clin_encounter',
        'ref_insurance_policy',
        'cmn_patient',
        'cmn_provider',
        'cmn_location'
    ]
    
    print("Cleaning Database...")
    try:
        for t in tables:
            print(f"  Truncating {t}...")
            cur.execute(f"TRUNCATE TABLE tebra.{t} CASCADE")
        conn.commit()
        print("Database Cleaned Successfully.")
    except Exception as e:
        print(f"Error cleaning DB: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    clean_db()
