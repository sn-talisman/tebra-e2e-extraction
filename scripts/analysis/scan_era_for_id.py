from src.connection import get_connection

TARGET_GUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'
ERA_FILENAME = 'P05536D260228494U1947-26031B100001685400.RMT'

# internal IDs we know exist for this claim (from previous PM_CLAIM inspection)
KNOWN_CLAIM_ID = '598543'
KNOWN_ENC_PROC_ID = '611270'
KNOWN_PATIENT_GUID = 'B8989E51-5135-43F4-B4DF-0DA427FC20CE'

def scan_era():
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"Fetching content for ERA: {ERA_FILENAME}")
    
    query = f"""
    SELECT FILECONTENTS 
    FROM PM_CLEARINGHOUSERESPONSE 
    WHERE PRACTICEGUID = '{TARGET_GUID}' 
      AND FILENAME = '{ERA_FILENAME}'
    LIMIT 1
    """
    
    cursor.execute(query)
    row = cursor.fetchone()
    
    if not row:
        print("ERA File not found!")
        return

    content = row[0]
    print(f"Content Length: {len(content)} chars")
    
    # Search for known keys
    targets = {
        'ClaimID': KNOWN_CLAIM_ID,
        'EncounterProcedureID': KNOWN_ENC_PROC_ID,
        'PatientGUID': KNOWN_PATIENT_GUID
    }
    
    print("\n--- Search Results ---")
    found_any = False
    for k, v in targets.items():
        if v in content:
            print(f"MATCH FOUND for {k}: {v}")
            # Find context
            idx = content.find(v)
            start = max(0, idx - 50)
            end = min(len(content), idx + 50)
            print(f"  Context: ...{content[start:end]}...")
            found_any = True
        else:
             print(f"No match for {k}: {v}")
             
    if not found_any:
        print("\nNo internal legacy IDs found in the 835 file.")
        print("Dumping first 500 chars for manual check of headers:")
        print(content[:500])

if __name__ == "__main__":
    scan_era()
