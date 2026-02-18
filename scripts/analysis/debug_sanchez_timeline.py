import logging
from src.connection import get_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_GUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'

def debug_sanchez():
    conn = get_connection()
    cursor = conn.cursor()

    # Broad search for Sanchez in file contents to catch all claim versions
    query = f"""
    SELECT 
        FILERECEIVEDATE, 
        CLEARINGHOUSERESPONSETYPENAME, 
        CLEARINGHOUSERESPONSEREPORTTYPENAME,
        FILENAME,
        REJECTED,
        DENIED,
        TITLE
    FROM PM_CLEARINGHOUSERESPONSE
    WHERE PRACTICEGUID = '{TARGET_GUID}'
      AND FILERECEIVEDATE >= '2026-01-20'
      AND FILECONTENTS LIKE '%SANCHEZ%'
    ORDER BY FILERECEIVEDATE ASC
    """
    
    logger.info("Querying history for 'SANCHEZ'...")
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"{'DATE':<20} | {'TYPE':<30} | {'REPORT':<15} | {'REJ':<3} | {'FILE':<30}")
    print("-" * 110)
    
    for row in rows:
        date, rtype, report_type, filename, rej, den, title = row
        print(f"{str(date):<20} | {rtype[:30]:<30} | {report_type[:15]:<15} | {rej:<3} | {filename[:30]}")

if __name__ == "__main__":
    debug_sanchez()
