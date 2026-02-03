import psycopg2
import json

DB_CONFIG = {
    "dbname": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password",
    "host": "localhost",
    "port": "5432"
}

ENC_ID = '388650'

def inspect_data():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print(f"--- Inspecting Encounter {ENC_ID} ---")
    
    # 1. Check Encounter Row (FKs)
    cur.execute("SELECT patient_guid, provider_guid, location_guid FROM tebra.clin_encounter WHERE encounter_id = %s", (ENC_ID,))
    enc = cur.fetchone()
    if enc:
        pat_guid, prov_guid, loc_guid = enc
        print(f"Encounter FKs:\n  PatientGUID: {pat_guid}\n  ProviderGUID: {prov_guid}\n  LocationGUID: {loc_guid}")
        
        # 2. Check Patient Table
        print("\n--- Patient Table ---")
        if pat_guid:
            cur.execute("SELECT * FROM tebra.cmn_patient WHERE patient_guid = %s", (pat_guid,))
            row = cur.fetchone()
            # Get columns
            cols = [desc[0] for desc in cur.description]
            print(dict(zip(cols, row)) if row else "Row not found")
            
        # 3. Check Provider Table
        print("\n--- Provider Table ---")
        if prov_guid:
            cur.execute("SELECT * FROM tebra.cmn_provider WHERE provider_guid = %s", (prov_guid,))
            row = cur.fetchone()
            cols = [desc[0] for desc in cur.description]
            print(dict(zip(cols, row)) if row else "Row not found")
        else:
             print("Provider GUID is NULL in Encounter table.")
             
        # 4. Check Location Table
        print("\n--- Location Table ---")
        if loc_guid:
            cur.execute("SELECT * FROM tebra.cmn_location WHERE location_guid = %s", (loc_guid,))
            row = cur.fetchone()
            cols = [desc[0] for desc in cur.description]
            print(dict(zip(cols, row)) if row else "Row not found")
        else:
            print("Location GUID is NULL in Encounter table.")

    else:
        print("Encounter not found in DB.")

    conn.close()

if __name__ == "__main__":
    inspect_data()
