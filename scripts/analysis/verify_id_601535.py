from src.connection import get_connection

TARGET_GUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'
TEST_ID = '601535'

def verify_id():
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"Testing Link via REF*6R: {TEST_ID}")
    
    query = f"""
    SELECT *
    FROM PM_ENCOUNTERPROCEDURE
    WHERE PRACTICEGUID = '{TARGET_GUID}' 
      AND ENCOUNTERPROCEDUREID = '{TEST_ID}'
    """
    
    cursor.execute(query)
    row = cursor.fetchone()
    
    if row:
        print(f"!!! MATCH FOUND for {TEST_ID} !!!")
        print(row)
    else:
        print(f"No match for {TEST_ID}")

if __name__ == "__main__":
    verify_id()
