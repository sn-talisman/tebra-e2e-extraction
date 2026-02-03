from src.connection import get_connection

TARGET_GUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'
TEST_ID = '601535'

def check_claim():
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"Checking PM_CLAIM for CLAIMID = {TEST_ID}")
    
    query = f"""
    SELECT *
    FROM PM_CLAIM
    WHERE PRACTICEGUID = '{TARGET_GUID}' 
      AND CLAIMID = '{TEST_ID}'
    """
    
    cursor.execute(query)
    row = cursor.fetchone()
    
    if row:
        print(f"!!! MATCH FOUND in PM_CLAIM !!!")
        
        # Get columns to print nice output
        cursor.execute("DESCRIBE TABLE PM_CLAIM")
        cols = [r[0] for r in cursor.fetchall()]
        data = dict(zip(cols, row))
        
        print(f"ClaimID: {data.get('CLAIMID')}")
        print(f"PatientGUID: {data.get('PATIENTGUID')}")
        print(f"EncounterProcID: {data.get('ENCOUNTERPROCEDUREID')}")
        print(f"CreatedDate: {data.get('CREATEDDATE')}")
    else:
        print(f"No match in PM_CLAIM for {TEST_ID}")

if __name__ == "__main__":
    check_claim()
