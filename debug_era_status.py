from src.connection import get_connection

def check_status_values():
    conn = get_connection()
    cursor = conn.cursor()
    
    print("--- Checking Distinct Status Values in tebra.fin_claim_line ---")
    
    query = """
    SELECT DISTINCT payer_status, claim_status
    FROM tebra.fin_claim_line
    LIMIT 20
    """
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            print(f"Payer Status: '{row[0]}', Claim Status: '{row[1]}'")
            
    except Exception as e:
        print(f"Error querying status: {e}")

    print("\n--- Checking Specific Claim 601535 (from check_claim_601535.py) in fin_claim_line ---")
    # Assuming tebra_claim_id corresponds to the claim ID
    query_claim = """
    SELECT *
    FROM tebra.fin_claim_line
    WHERE tebra_claim_id = '601535'
    """
    try:
        cursor.execute(query_claim)
        row = cursor.fetchone()
        if row:
            print("Found in fin_claim_line!")
            print(row)
        else:
            print("NOT FOUND in fin_claim_line.")
    except Exception as e:
        print(f"Error querying claim: {e}")

    conn.close()

if __name__ == "__main__":
    check_status_values()
