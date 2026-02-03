from src.connection import get_connection

TARGET_GUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'

def debug_join():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Found Miriam Gunter earlier: 627557A9-8DAA-48A0-9D7E-9C8EFA6B0E37
    p_guid = '627557A9-8DAA-48A0-9D7E-9C8EFA6B0E37'
    print(f"Using Known Patient GUID: {p_guid}")
    
    enc_query = f"""
    SELECT 
       E.ENCOUNTERID, 
       E.ENCOUNTERGUID, 
       E.DATEOFSERVICE, 
       E.PATIENTGUID,
       E.PROVIDERGUID,
       E.APPOINTMENTGUID,
       D.FIRSTNAME as PROV_FIRST,
       D.LASTNAME as PROV_LAST,
       D.NPI,
       A.APPOINTMENTTYPE,
       A.SUBJECT as APPT_REASON
   FROM PM_ENCOUNTER E
   LEFT JOIN PM_DOCTOR D ON E.PROVIDERGUID = D.DOCTORGUID
   LEFT JOIN PM_APPOINTMENT A ON E.APPOINTMENTGUID = A.APPOINTMENTGUID
   WHERE E.PRACTICEGUID = '{TARGET_GUID}'
     AND E.PATIENTGUID = '{p_guid}'
   LIMIT 5
   """
    
    print("Executing Encounter Join Query...")
    try:
        cursor.execute(enc_query)
        rows = cursor.fetchall()
        
        if not rows:
            print("No Encounters found for Miriam.")
            return

        print(f"\nFound {len(rows)} Encounters (Joined with Doctor/Appt):")
        print(f"{'Date':<12} | {'Provider':<20} | {'Appt Type':<20} | {'Reason':<20}")
        print("-" * 80)
        for r in rows:
            # Row indices: 2=Date, 6=First, 7=Last, 9=Type, 10=Reason
            dos = str(r[2])[:10]
            prov = f"{r[6] or ''} {r[7] or ''}"
            appt = f"{r[9] or ''}"
            reason = f"{r[10] or ''}"
            print(f"{dos:<12} | {prov:<20} | {appt:<20} | {reason:<20}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_join()
