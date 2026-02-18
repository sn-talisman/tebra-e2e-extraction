import psycopg2
from src.connection import get_connection as get_sf_conn

# Postgres Connection Params
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

def sync_practices():
    print("Connecting to Snowflake...")
    sf_conn = get_sf_conn()
    sf_cur = sf_conn.cursor()
    
    # Get Active Practices
    sf_cur.execute("""
        SELECT DISTINCT p.PRACTICEGUID, p.NAME
        FROM PM_PRACTICE p
        WHERE p.ACTIVE = TRUE
    """)
    practices = sf_cur.fetchall()
    print(f"Found {len(practices)} Active Practices in Snowflake.")
    sf_conn.close()
    
    if not practices:
        print("No practices found.")
        return

    print("Connecting to Postgres...")
    pg_conn = get_pg_conn()
    pg_cur = pg_conn.cursor()
    
    inserted = 0
    for guid, name in practices:
        sql = """
            INSERT INTO tebra.cmn_practice (practice_guid, name, active)
            VALUES (%s, %s, TRUE)
            ON CONFLICT (practice_guid) DO UPDATE
            SET name = EXCLUDED.name
        """
        try:
            pg_cur.execute(sql, (guid, name))
            inserted += 1
        except Exception as e:
            print(f"Error inserting {name}: {e}")
            pg_conn.rollback() # Rollback transaction part
            
    pg_conn.commit()
    pg_conn.close()
    
    print(f"Successfully synced {inserted} practices to 'tebra.cmn_practice'.")

if __name__ == "__main__":
    sync_practices()
