from src.connection import get_connection

def dump_schemas():
    conn = get_connection()
    cur = conn.cursor()
    
    tables = [
        'PM_ENCOUNTER', 
        'PM_CLAIM', 
        'PM_ENCOUNTERPROCEDURE', 
        'PM_PATIENT', 
        'PM_INSURANCEPOLICY',
        'PM_DOCTOR',
        'PM_SERVICELOCATION'
    ]
    
    with open('schema_dump.txt', 'w') as f:
        for t in tables:
            f.write(f"\n=== {t} ===\n")
            try:
                cur.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{t}' ORDER BY ORDINAL_POSITION")
                cols = cur.fetchall()
                for c, dtype in cols:
                    f.write(f"{c} ({dtype})\n")
            except Exception as e:
                f.write(f"Error: {e}\n")
                
    conn.close()
    print("Schema dumped to schema_dump.txt")

if __name__ == "__main__":
    dump_schemas()
