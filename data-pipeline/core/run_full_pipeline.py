import os
import sys

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import psycopg2
from extraction.extract_batch_optimized import extract_batch
from extraction.extract_eras_rejections import extract_rejections
from loading.load_to_postgres import load_practice_data, DB_CONFIG

def reset_db():
    print("--- TRUNCATING DATABASE TABLES ---")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    tables = [
        'tebra.fin_claim_line', 'tebra.clin_encounter_diagnosis', 'tebra.clin_encounter',
        'tebra.fin_era_bundle', 'tebra.fin_era_report', 'tebra.ref_insurance_policy',
        'tebra.cmn_location', 'tebra.cmn_provider', 'tebra.cmn_patient', 'tebra.cmn_practice'
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
        
        # Parse Practice Name and GUID from directory name (Format: NAME_GUID)
        try:
            parts = p.rsplit('_', 1)
            if len(parts) == 2:
                p_name = parts[0].replace('_', ' ')
                p_guid = parts[1]
            else:
                p_name = p
                p_guid = None
        except:
            p_name = p
            p_guid = None
            
        try:
            # Step A: Extract
            print(f"  -> Extracting {p_name}...")
            extract_batch(p_dir, p_dir)
            
            # Step B: Load
            print(f"  -> Loading {p_name}...")
            load_practice_data(p_dir, practice_guid=p_guid, practice_name=p_name)
            
        except Exception as e:
            print(f"!!! Error processing {p}: {e}")

if __name__ == "__main__":
    run_pipeline()
