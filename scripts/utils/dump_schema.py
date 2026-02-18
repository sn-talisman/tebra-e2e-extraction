from src.connection import get_connection

def dump_schema():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check PM_CLAIM full
    print("--- PM_CLAIM Full Schema ---")
    try:
        cursor.execute("DESCRIBE TABLE PM_CLAIM")
        cols = [row[0] for row in cursor.fetchall()]
        print(cols)
    except Exception as e: print(e)

    # Check PM_ENCOUNTER full
    print("\n--- PM_ENCOUNTER Full Schema ---")
    try:
        cursor.execute("DESCRIBE TABLE PM_ENCOUNTER")
        cols = [row[0] for row in cursor.fetchall()]
        print(cols)
    except Exception as e: print(e)

    # Probe tables
    print("\n--- Probing Tables ---")
    for t in ['PM_CARRIER', 'PM_INSURANCECARRIER', 'PM_PAYER', 'PM_INSURANCEPLAN', 'PM_PATIENTINSURANCE']:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t} LIMIT 1")
            print(f"  {t}: Exists")
        except:
            print(f"  {t}: Not Found")

if __name__ == "__main__":
    dump_schema()
