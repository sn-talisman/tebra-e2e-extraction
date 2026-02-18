"""
Update fin_claim_line with practice_guid extracted from directory names.
"""
import psycopg2
from glob import glob
import os

DB_CONFIG = {
    "host": "localhost",
    "database": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password"
}

def update_practice_guids():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # First ensure the column exists
    cur.execute("ALTER TABLE tebra.fin_claim_line ADD COLUMN IF NOT EXISTS practice_guid UUID;")
    conn.commit()
    
    # Find all service_lines.csv files and extract practice GUIDs
    csv_files = glob("output_all_practices/*/service_lines.csv")
    
    for csv_file in csv_files:
        dir_name = os.path.basename(os.path.dirname(csv_file))
        # Extract GUID from dir name like "PERFORMANCE_REHABILITATION_CORP_EE5ED349-D9DD-4BF5-81A5-AA503A261961"
        parts = dir_name.split('_')
        guid_part = parts[-1] if len(parts) > 1 else None
        
        # Check if last part looks like a GUID (contains hyphens and is right length)
        if guid_part and len(guid_part) == 36 and '-' in guid_part:
            practice_guid = guid_part.lower()
            
            # Count claims for this practice based on claim_reference pattern
            # Extract practice name for logging
            practice_name = '_'.join(parts[:-1]) if len(parts) > 1 else dir_name
            
            # Claims were loaded with unique IDs based on row position
            # We need to update based on the claim_reference_id pattern matching ERA bundles for this practice
            
            # Get ERA bundles for this practice
            cur.execute("""
                UPDATE tebra.fin_claim_line cl
                SET practice_guid = %s
                FROM tebra.fin_era_bundle eb
                WHERE cl.claim_reference_id = eb.claim_reference_id
                AND eb.practice_guid = %s
            """, (practice_guid, practice_guid))
            
            rows_updated = cur.rowcount
            print(f"  {practice_name}: Updated {rows_updated} claims with practice_guid")
    
    conn.commit()
    
    # Now check how many have practice_guid set
    cur.execute("SELECT COUNT(*) FROM tebra.fin_claim_line WHERE practice_guid IS NOT NULL")
    with_guid = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM tebra.fin_claim_line")
    total = cur.fetchone()[0]
    
    print(f"\n=== Summary: {with_guid}/{total} claims have practice_guid ===")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    update_practice_guids()
