from src.connection import get_connection

def check_mod_schema():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PM_PROCEDUREMODIFIER' ORDER BY ORDINAL_POSITION")
    for r in cur.fetchall():
        print(f"{r[0]} ({r[1]})")
    conn.close()

if __name__ == "__main__":
    check_mod_schema()
