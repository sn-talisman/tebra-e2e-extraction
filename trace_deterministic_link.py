from src.connection import get_connection

TARGET_GUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'
INTERNAL_CLAIM_ID = '598543'
ERA_EXTERNAL_ID = '388506Z43267'
ERA_SUBSTRING = '388506'

def trace_link():
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"--- Deep Inspection of PM_CLAIM for ID: {INTERNAL_CLAIM_ID} ---")
    
    # 1. Get all columns for PM_CLAIM schema
    cursor.execute("DESCRIBE TABLE PM_CLAIM")
    schema = cursor.fetchall()  # [(name, type...), ...]
    cols = [r[0] for r in schema]
    
    # 2. Fetch the specific row
    query = f"SELECT * FROM PM_CLAIM WHERE PRACTICEGUID = '{TARGET_GUID}' AND CLAIMID = '{INTERNAL_CLAIM_ID}'"
    cursor.execute(query)
    row = cursor.fetchone()
    
    if not row:
        print("Error: Could not find the Internal Claim ID row to inspect.")
        return

    # 3. Inspect every value
    print(f"Row found. Scanning {len(cols)} columns for matches to ERA ID '{ERA_EXTERNAL_ID}'...")
    
    match_found = False
    row_dict = dict(zip(cols, row))
    
    for col, val in row_dict.items():
        val_str = str(val) if val is not None else ""
        
        # Check Exact Match
        if val_str == ERA_EXTERNAL_ID:
            print(f"!!! EXACT MATCH FOUND !!!")
            print(f"Column: {col}")
            print(f"Value:  {val}")
            match_found = True
            
        # Check Substring Match
        elif ERA_SUBSTRING in val_str:
            print(f"!!! SUBSTRING MATCH FOUND !!!")
            print(f"Column: {col}")
            print(f"Value:  {val}")
            match_found = True
            
    if not match_found:
        print("No direct text match found in PM_CLAIM row.")
        print("Dumping non-null columns for manual review:")
        for k, v in row_dict.items():
            if v:
                print(f"{k}: {v}")
                
    # 4. Check PM_CLEARINGHOUSERESPONSE for the reverse link?
    # Maybe the ERA table has the ClaimID?
    print("\n--- Checking ERA Table for Internal ID ---")
    # We need to find the ERA file record first.
    # We know the Filename from previous steps: 'P05536D260228494U1947-26031B100001685400.RMT' (from csv head)
    
    era_filename = 'P05536D260228494U1947-26031B100001685400.RMT'
    
    cq = f"""
    SELECT * FROM PM_CLEARINGHOUSERESPONSE 
    WHERE PRACTICEGUID = '{TARGET_GUID}' 
      AND FILENAME = '{era_filename}'
    LIMIT 1
    """
    cursor.execute(cq)
    erow = cursor.fetchone()
    if erow:
        cursor.execute("DESCRIBE TABLE PM_CLEARINGHOUSERESPONSE")
        ecols = [r[0] for r in cursor.fetchall()]
        edict = dict(zip(ecols, erow))
        
        # Check if Internal ID is in ERA table
        for col, val in edict.items():
            if str(val) == INTERNAL_CLAIM_ID:
                 print(f"!!! FOUND INTERNAL ID IN ERA TABLE !!!")
                 print(f"Column: {col} = {val}")
    else:
        print(f"ERA File {era_filename} not found in DB.")

if __name__ == "__main__":
    trace_link()
