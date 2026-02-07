import logging
import json
from src.connection import get_connection

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_schema():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Inspect Columns of PM_CLEARINGHOUSERESPONSE
        logger.info("--- Inspecting PM_CLEARINGHOUSERESPONSE Columns ---")
        cursor.execute("SELECT TOP 1 * FROM PM_CLEARINGHOUSERESPONSE")
        row = cursor.fetchone()
        if row:
            # Snowflake cursor.description contains column metadata
            columns = [col[0] for col in cursor.description]
            print(f"Columns: {json.dumps(columns, indent=2)}")
        else:
            print("Table is empty.")

        # 2. Search for other relevant tables
        logger.info("\n--- Searching for ERA-related Tables ---")
        # Note: This query depends on permissions. 
        # listing tables usually requires SHOW TABLES or querying INFORMATION_SCHEMA
        try:
            cursor.execute("SHOW TABLES LIKE 'PM_%'")
            tables = cursor.fetchall()
            # Table name is usually index 1 in SHOW output
            pm_tables = [t[1] for t in tables]
            print(f"Found PM_ Tables: {pm_tables}")
            
            cursor.execute("SHOW TABLES LIKE 'FIN_%'")
            tables = cursor.fetchall()
            fin_tables = [t[1] for t in tables]
            print(f"Found FIN_ Tables: {fin_tables}")
        except Exception as e:
            print(f"Could not list tables: {e}")

    except Exception as e:
        logger.error(f"Connection failed: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    inspect_schema()
