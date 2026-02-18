import csv
from src.connection import get_connection

def debug_claims():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Check Schema of PM_CLAIM
    print("--- PM_CLAIM Columns ---")
    try:
        cursor.execute("SELECT TOP 1 * FROM PM_CLAIM")
        cols = [d[0] for d in cursor.description]
        print(cols)
    except Exception as e:
        print(f"Error describing PM_CLAIM: {e}")

    # 2. Get a sample of IDs from service_lines.csv
    ids_to_check = []
    with open('service_lines.csv', 'r') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i < 10: ids_to_check.append(row['LineID_Ref6R'])

    print(f"\n--- Checking {len(ids_to_check)} IDs ---")
    for lid in ids_to_check:
        print(f"Checking ID: {lid}")
        # Try finding it in various columns
        q = f"""
        SELECT CLAIMID, CLAIMNUMBER, PATIENTGUID 
        FROM PM_CLAIM 
        WHERE CLAIMID = '{lid}' OR CLAIMNUMBER = '{lid}'
        """
        cursor.execute(q)
        row = cursor.fetchone()
        if row:
            print(f"  FOUND! ClaimID={row[0]}, Number={row[1]}")
        else:
            print(f"  NOT FOUND via ID/Number.")

    conn.close()

if __name__ == "__main__":
    debug_claims()
