"""
Search for specific Claim ID in all ERAs.
Target Claim ID: 389119Z43267
"""
from src.connection import get_connection

TARGET_CLAIM_ID = "389119Z43267"

def search_claim():
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"Searching for Claim ID: {TARGET_CLAIM_ID} in PM_CLEARINGHOUSERESPONSE...")
    
    # We need to search FILECONTENTS for the string.
    # Note: This is slow if table is huge, but for a single practice GUID it might be okay.
    # Ideally use Snowflake's search if available or just LIKE.
    
    query = f"""
    SELECT FILERECEIVEDATE, FILENAME, CLEARINGHOUSERESPONSETYPENAME 
    FROM PM_CLEARINGHOUSERESPONSE 
    WHERE PRACTICEGUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'
      AND FILECONTENTS LIKE '%{TARGET_CLAIM_ID}%'
    ORDER BY FILERECEIVEDATE DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"Found {len(results)} matches:")
    for row in results:
        print(f" - {row[0]} | {row[1]} | {row[2]}")

if __name__ == "__main__":
    search_claim()
