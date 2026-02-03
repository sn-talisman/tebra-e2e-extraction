from src.connection import get_connection

def hunt_id():
    conn = get_connection()
    cur = conn.cursor()
    target_id = '713793'
    
    # List candidate tables
    tables = [
        ('PM_ICD10DIAGNOSISCODEDICTIONARY', 'ICD10DIAGNOSISCODEDICTIONARYID'),
        ('PM_DIAGNOSISCODEDICTIONARY', 'DIAGNOSISCODEDICTIONARYID'),
        ('PM_ENCOUNTERDIAGNOSIS', 'ENCOUNTERDIAGNOSISID'), 
        ('PM_ICD10CODEDIAGNOSISCATEGORY', 'ICD10DIAGNOSISCODECATEGORYID')
    ]
    
    print(f"--- Hunting for ID {target_id} ---")
    for t, col in tables:
        try:
            cur.execute(f"SELECT * FROM {t} WHERE {col} = '{target_id}'")
            if cur.fetchone():
                print(f"FOUND IN: {t} (Column: {col})")
                
                # If found, show columns to see where description might be
                cur.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{t}' ORDER BY ORDINAL_POSITION")
                cols = [r[0] for r in cur.fetchall()]
                print(f"Columns: {', '.join(cols)}")
                return
        except Exception as e:
            print(f"Error checking {t}: {e}")

    print("ID Not found in candidate tables.")
    conn.close()

if __name__ == "__main__":
    hunt_id()
