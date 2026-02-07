import os
import sys
import psycopg2
import snowflake.connector
from src.connection import get_connection as get_sf_conn

# Postgres Connection Params (matching load_to_postgres.py)
PG_HOST = "localhost"
PG_DB = "tebra_dw"
PG_USER = "tebra_user"
PG_PASS = "tebra_password"

def get_pg_conn():
    return psycopg2.connect(
        host=PG_HOST,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASS
    )

def verify():
    print("============================================================")
    print("VERIFICATION: Postgres vs Snowflake (Active Practices)")
    print("============================================================")

    # 1. Postgres Counts
    print("Querying Postgres...")
    pg_conn = get_pg_conn()
    pg_cur = pg_conn.cursor()
    
    pg_cur.execute("SELECT COUNT(*) FROM tebra.fin_era_report")
    pg_eras = pg_cur.fetchone()[0]
    
    pg_cur.execute("SELECT COUNT(*) FROM tebra.clin_encounter")
    pg_encs = pg_cur.fetchone()[0]
    
    pg_cur.execute("SELECT COUNT(*) FROM tebra.fin_claim_line")
    pg_lines = pg_cur.fetchone()[0]
    
    pg_conn.close()
    
    print(f"  -> ERAs Loaded: {pg_eras}")
    print(f"  -> Encounters Loaded: {pg_encs}")
    print(f"  -> Claim Lines Loaded: {pg_lines}")
    
    # 2. Snowflake Counts
    print("\nQuerying Snowflake (Source of Truth)...")
    sf_conn = get_sf_conn()
    sf_cur = sf_conn.cursor()
    
    # Get Active Practice GUIDs (Same Scope as Orchestrator)
    print("  -> Fetching Active Practice List...")
    sf_cur.execute("""
        SELECT DISTINCT P.PRACTICEGUID 
        FROM PM_PRACTICE P
        JOIN PM_CLEARINGHOUSERESPONSE C ON P.PRACTICEGUID = C.PRACTICEGUID
        WHERE P.ACTIVE = TRUE
    """)
    active_guids = [row[0] for row in sf_cur.fetchall()]
    print(f"  -> Identified {len(active_guids)} Active Practices with Data.")
    
    if not active_guids:
        print("No active practices found? Something is wrong.")
        return

    # Construct WHERE clause
    guid_list = "', '".join(active_guids)
    
    # Count Active ERAs (Since 2025-08-08 as per Orchestrator)
    print("  -> Counting ERAs (since 2025-08-08)...")
    sf_cur.execute(f"""
        SELECT COUNT(*) 
        FROM PM_CLEARINGHOUSERESPONSE 
        WHERE PRACTICEGUID IN ('{guid_list}')
        AND FILERECEIVEDATE >= '2025-08-08'
    """)
    sf_eras = sf_cur.fetchone()[0]
    
    sf_conn.close()
    
    print(f"  -> Source ERAs: {sf_eras}")
    
    # 3. Comparison
    print("\n============================================================")
    print("RESULTS")
    print("============================================================")
    
    diff = sf_eras - pg_eras
    match = (diff == 0)
    
    print(f"ERAs (Reports):")
    print(f"  Source (Snowflake): {sf_eras}")
    print(f"  Target (Postgres):  {pg_eras}")
    print(f"  Difference:         {diff}")
    
    if match:
        print("✅ SUCCESS: ERA Count Matches Exactly!")
    else:
        print("⚠️ WARNING: Mismatch in ERA counts.")
        if diff > 0:
            print(f"  Missing {diff} ERAs in Postgres.")
        else:
            print(f"  Postgres has {abs(diff)} MORE ERAs? (Duplicates?)")
            
    print("\nOperational Metrics:")
    print(f"  Encounters Enriched: {pg_encs}")
    print(f"  Lines Linked:        {pg_lines}")
    print("============================================================")

if __name__ == "__main__":
    verify()
