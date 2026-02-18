from src.connection import get_connection

TARGET_GUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'
TEST_LINE_ID = '600408' # From service_lines.csv (REF*6R)

def verify_line_link():
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"Testing Deterministic Link via REF*6R: {TEST_LINE_ID}")
    
    # Check PM_ENCOUNTERPROCEDURE for this ID
    query = f"""
    SELECT 
        EP.ENCOUNTERPROCEDUREID,
        EP.ENCOUNTERGUID,
        EP.PROCEDUREDATEOFSERVICE,
        EP.SERVICECHARGEAMOUNT
    FROM PM_ENCOUNTERPROCEDURE EP
    WHERE EP.PRACTICEGUID = '{TARGET_GUID}' 
      AND EP.ENCOUNTERPROCEDUREID = '{TEST_LINE_ID}'
    """
    
    print("Executing query on PM_ENCOUNTERPROCEDURE...")
    try:
        cursor.execute(query)
        row = cursor.fetchone()
        
        if row:
            print(f"!!! MATCH FOUND !!!")
            print(f"EncounterProcedureID: {row[0]}")
            print(f"EncounterGUID: {row[1]}")
            print(f"Date: {row[2]}")
            print(f"Amount: {row[3]}")
            
            # Now can we trace back to CLAIM/PATIENT?
            # Usually via EncounterGUID -> PM_ENCOUNTER -> PatientGUID
            
            eng_guid = row[1]
            q2 = f"""
            SELECT E.ENCOUNTERID, E.PATIENTGUID, P.FIRSTNAME, P.LASTNAME
            FROM PM_ENCOUNTER E
            JOIN PM_PATIENT P ON E.PATIENTGUID = P.PATIENTGUID
            WHERE E.PRACTICEGUID = '{TARGET_GUID}'
              AND E.ENCOUNTERGUID = '{eng_guid}'
            """
            cursor.execute(q2)
            r2 = cursor.fetchone()
            if r2:
                print(f"  -> Linked to Patient: {r2[2]} {r2[3]} (EncID: {r2[0]})")
            else:
                print("  -> Could not link Encounter to Patient.")
        else:
            print(f"No match found for EncounterProcedureID {TEST_LINE_ID}")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_line_link()
