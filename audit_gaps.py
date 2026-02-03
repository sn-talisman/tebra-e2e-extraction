from src.connection import get_connection

def audit_schema():
    conn = get_connection()
    cur = conn.cursor()
    
    # Tables we rely on heavily
    core_tables = ['PM_ENCOUNTER', 'PM_CLAIM', 'PM_ENCOUNTERPROCEDURE']
    
    print("=== SCHEMA GAP AUDIT ===")
    
    for t in core_tables:
        print(f"\n--- {t} ---")
        try:
            # Get all columns
            cur.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{t}' ORDER BY ORDINAL_POSITION")
            cols = [r[0] for r in cur.fetchall()]
            
            # Highlight potential FKs (ending in ID or CODE)
            potential_fks = [c for c in cols if (c.endswith('ID') or c.endswith('CODE') or c.endswith('GUID')) and not c.startswith('CREATED') and not c.startswith('MODIFIED')]
            
            print(f"Total Columns: {len(cols)}")
            print("Potential Foreign Keys / Codes:")
            for k in potential_fks:
                print(f"  - {k}")
        except Exception as e:
            print(f"Error reading {t}: {e}")
            
    conn.close()

if __name__ == "__main__":
    audit_schema()
