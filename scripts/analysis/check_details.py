from src.connection import get_connection

def check_more_schemas():
    conn = get_connection()
    cur = conn.cursor()
    
    tables = ['PM_ENCOUNTERPROCEDURE', 'PM_APPOINTMENT', 'PM_PROCEDUREMODIFIER', 'PM_PLACEOFSERVICE']
    
    for t in tables:
        print(f"\n--- {t} ---")
        try:
            cur.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{t}' ORDER BY ORDINAL_POSITION")
            cols = [r[0] for r in cur.fetchall()]
            print(", ".join(cols))
        except Exception as e:
            print(f"Error: {e}")
            
    conn.close()

if __name__ == "__main__":
    check_more_schemas()
