import os
import glob
import psycopg2
from extract_batch_optimized import extract_batch
from load_to_postgres import load_practice_data, DB_CONFIG

def reset_db():
    print("--- TRUNCATING DATABASE TABLES ---")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    tables = [
        'tebra.fin_claim_line', 'tebra.clin_encounter_diagnosis', 'tebra.clin_encounter',
        'tebra.ref_insurance_policy', 'tebra.cmn_location', 'tebra.cmn_provider', 'tebra.cmn_patient',
        'tebra.fin_era_bundle'
    ]
    try:
        cur.execute("TRUNCATE TABLE " + ", ".join(tables) + " CASCADE;")
        conn.commit()
        print("Tables truncated successfully.")
    except Exception as e:
        print(f"Error truncating tables: {e}")
        conn.rollback()
    finally:
        conn.close()

def run_pipeline():
    # 1. Cleaner
    reset_db()
    
    # 2. Iterate
    base_dir = '/Users/ssnesargi/Documents/Code/tebra-e2e-extraction/output_all_practices'
    practices = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]
    
    print(f"Found {len(practices)} practices to process.")
    
    for i, p in enumerate(sorted(practices)):
        p_dir = os.path.join(base_dir, p)
        print(f"\n[{i+1}/{len(practices)}] Processing: {p}...")
        
        try:
            # Step A: Extract
            print("  -> Extracting...")
            extract_batch(p_dir, p_dir)
            
            # Step B: Load
            print("  -> Loading...")
            load_practice_data(p_dir)
            
        except Exception as e:
            print(f"!!! Error processing {p}: {e}")

if __name__ == "__main__":
    run_pipeline()
