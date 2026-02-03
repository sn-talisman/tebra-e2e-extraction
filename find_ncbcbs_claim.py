"""
Search NC BCBS ERAs for 'Kelly' or '389119'.
Target: Find the file containing the missing claim.
"""
from src.connection import get_connection

def search_ncbcbs():
    conn = get_connection()
    cursor = conn.cursor()
    
    print("Searching ALL 'NC BCBS' ERAs for 'Kelly' or '389119'...")
    
    # We search for both strings. 
    # Note: 'Kelly' might be in NM1 segment. '389119' in CLP/CLP01.
    query = """
    SELECT FILERECEIVEDATE, FILENAME, FILECONTENTS
    FROM PM_CLEARINGHOUSERESPONSE 
    WHERE PRACTICEGUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'
      AND SOURCENAME = 'NC BCBS'
      AND CLEARINGHOUSERESPONSEREPORTTYPENAME = 'ERA'
      AND (FILECONTENTS LIKE '%Kelly%' OR FILECONTENTS LIKE '%389119%')
    ORDER BY FILERECEIVEDATE DESC
    LIMIT 10
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"Found {len(results)} matching files:")
    for row in results:
        date_str = row[0]
        fname = row[1]
        content = row[2]
        
        # Quick check found context
        context = []
        if 'Kelly' in content: context.append("Found 'Kelly'")
        if '389119' in content: context.append("Found '389119'")
        
        print(f" - {date_str} | {fname} |Matches: {', '.join(context)}")

if __name__ == "__main__":
    search_ncbcbs()
