from src.connection import get_connection

TARGET_ID = '713793'

def trace_linkage():
    conn = get_connection()
    cur = conn.cursor()
    
    print(f"--- Tracing {TARGET_ID} ---")
    
    # Step 1: Query PM_ENCOUNTERDIAGNOSIS
    q1 = f"SELECT * FROM PM_ENCOUNTERDIAGNOSIS WHERE ENCOUNTERDIAGNOSISID = '{TARGET_ID}'"
    print(f"Executing: {q1}")
    cur.execute(q1)
    row = cur.fetchone()
    
    if not row:
        print("Step 1 Failed: ID not found in PM_ENCOUNTERDIAGNOSIS")
        return

    # Get column names to find DIAGNOSISCODEDICTIONARYID
    cur.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PM_ENCOUNTERDIAGNOSIS' ORDER BY ORDINAL_POSITION")
    cols = [r[0] for r in cur.fetchall()]
    row_dict = dict(zip(cols, row))
    print("Step 1 Result:", row_dict)
    
    dict_id = row_dict.get('DIAGNOSISCODEDICTIONARYID')
    print(f"-> Dictionary ID: {dict_id}")
    
    if not dict_id:
        print("Step 1 Failed: Dictionary ID is Null")
        return

    # Step 2: Query Dictionary Tables
    print(f"\n--- Checking Dictionary ID {dict_id} ---")
    
    # Try ICD10
    q2 = f"SELECT * FROM PM_ICD10DIAGNOSISCODEDICTIONARY WHERE ICD10DIAGNOSISCODEDICTIONARYID = '{dict_id}'"
    print(f"Try ICD10: {q2}")
    cur.execute(q2)
    start_icd10 = cur.fetchone()
    if start_icd10:
        print("FOUND IN ICD10!")
        cur.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PM_ICD10DIAGNOSISCODEDICTIONARY' ORDER BY ORDINAL_POSITION")
        cols = [r[0] for r in cur.fetchall()]
        print(dict(zip(cols, start_icd10)))
    else:
        print("Not found in ICD10 table.")
        
    # Try Legacy
    q3 = f"SELECT * FROM PM_DIAGNOSISCODEDICTIONARY WHERE DIAGNOSISCODEDICTIONARYID = '{dict_id}'"
    print(f"Try Legacy: {q3}")
    cur.execute(q3)
    start_legacy = cur.fetchone()
    if start_legacy:
        print("FOUND IN Legacy!")
        cur.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PM_DIAGNOSISCODEDICTIONARY' ORDER BY ORDINAL_POSITION")
        cols = [r[0] for r in cur.fetchall()]
        print(dict(zip(cols, start_legacy)))
    else:
        print("Not found in Legacy table.")

    conn.close()

if __name__ == "__main__":
    trace_linkage()
