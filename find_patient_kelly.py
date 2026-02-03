"""
Search ALL ERAs for 'Kelly'.
Target: Locate the patient 'Kelly' in any 835 file.
"""
from src.connection import get_connection

def search_patient_global():
    conn = get_connection()
    cursor = conn.cursor()
    
    print("Searching ALL ERAs for 'Kelly' (any payer)...")
    
    query = """
    SELECT FILERECEIVEDATE, FILENAME, SOURCENAME
    FROM PM_CLEARINGHOUSERESPONSE 
    WHERE PRACTICEGUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'
      AND CLEARINGHOUSERESPONSEREPORTTYPENAME = 'ERA'
      AND FILECONTENTS LIKE '%Kelly%'
    ORDER BY FILERECEIVEDATE DESC
    LIMIT 20
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"Found {len(results)} matches:")
    for row in results:
        print(f" - {row[0]} | {row[1]} | Source: {row[2]}")

if __name__ == "__main__":
    search_patient_global()
