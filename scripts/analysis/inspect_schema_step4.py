from src.connection import get_connection

def inspect_schema():
    conn = get_connection()
    cursor = conn.cursor()
    
    tables = ['PM_ENCOUNTER', 'PM_ENCOUNTERPROCEDURE', 'PM_DOCTOR', 'PM_APPOINTMENT']
    
    for t in tables:
        print(f"\n--- {t} ---")
        try:
            # Snowflake DESCRIBE TABLE
            cursor.execute(f"DESCRIBE TABLE {t}")
            for row in cursor.fetchall():
                # row structure: name, type, kind, null?, default, primary key, unique key, check, expression, comment, policy name
                print(f"{row[0]} ({row[1]})")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    inspect_schema()
