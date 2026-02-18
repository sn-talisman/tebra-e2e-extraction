import logging
import json
from src.connection import get_connection

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sample_data():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        logger.info("--- Sampling ERA Columns ---")
        query = """
        SELECT 
            FILENAME, 
            CLEARINGHOUSERESPONSEREPORTTYPENAME, 
            DENIED, 
            REJECTED, 
            ITEMCOUNT, 
            TOTALAMOUNT 
        FROM PM_CLEARINGHOUSERESPONSE 
        WHERE CLEARINGHOUSERESPONSEREPORTTYPENAME = 'ERA'
        LIMIT 10
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if rows:
            print(f"{'FILENAME':<40} | {'TYPE':<5} | {'DEN':<5} | {'REJ':<5} | {'ITEMS':<5} | {'AMOUNT':<10}")
            print("-" * 90)
            for row in rows:
                # Handle None values
                fname = row[0] or ""
                rtype = row[1] or ""
                den = row[2] if row[2] is not None else "NULL"
                rej = row[3] if row[3] is not None else "NULL"
                items = row[4] if row[4] is not None else "NULL"
                amt = row[5] if row[5] is not None else "NULL"
                
                print(f"{fname[-40:]:<40} | {rtype:<5} | {str(den):<5} | {str(rej):<5} | {str(items):<5} | {str(amt):<10}")
        else:
            print("No ERA records found.")

    except Exception as e:
        logger.error(f"Sampling failed: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    sample_data()
