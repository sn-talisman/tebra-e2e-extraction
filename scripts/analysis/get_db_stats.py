import psycopg2
# from src.connection import get_db_connection 
import os

# Credentials from load_to_postgres.py
DB_HOST = "localhost"
DB_NAME = "tebra_dw"
DB_USER = "tebra_user"
DB_PASS = "tebra_password"
DB_PORT = "5432"

def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )

def run_counts():
    conn = get_conn()
    cur = conn.cursor()
    
    stats = {}
    
    # 1. Patients
    cur.execute("SELECT COUNT(*) FROM tebra.cmn_patient")
    stats['Patients'] = cur.fetchone()[0]
    
    # 2. Providers
    cur.execute("SELECT COUNT(*) FROM tebra.cmn_provider")
    stats['Providers'] = cur.fetchone()[0]
    
    # 3. Insurance Agencies (Distinct Names)
    cur.execute("SELECT COUNT(DISTINCT company_name) FROM tebra.ref_insurance_policy")
    stats['Insurance Agencies'] = cur.fetchone()[0]
    
    # 4. Encounters
    cur.execute("SELECT COUNT(*) FROM tebra.clin_encounter")
    stats['Encounters'] = cur.fetchone()[0]
    
    # 5. Claims (Distinct Claim IDs from lines)
    cur.execute("SELECT COUNT(DISTINCT tebra_claim_id) FROM tebra.fin_claim_line")
    stats['Claims'] = cur.fetchone()[0]
    
    # Practices: Not stored in DB as entity, derived from Orchestrator runs.
    stats['Practices'] = "28 (from execution report)" 

    conn.close()
    
    print("\n=== Database Statistics ===")
    for k, v in stats.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    run_counts()
