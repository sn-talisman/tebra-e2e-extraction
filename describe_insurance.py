from src.connection import get_connection

def describe_insurance_chain():
    conn = get_connection()
    cursor = conn.cursor()
    
    tables = [
        'PM_INSURANCEPOLICY',
        'PM_INSURANCECOMPANY',
        'PM_INSURANCEPOLICYAUTHORIZATION',
        'PM_PATIENTCASE'
    ]
    
    for t in tables:
        print(f"\n--- {t} ---")
        try:
            cursor.execute(f"DESCRIBE TABLE {t}")
            cols = [row[0] for row in cursor.fetchall()]
            print(cols)
        except Exception as e: print(e)

if __name__ == "__main__":
    describe_insurance_chain()
