from src.connection import get_connection

def list_all_tables():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SHOW TABLES")
        tables = [row[1] for row in cursor.fetchall()]
        print(f"Total Tables: {len(tables)}")
        # Filter for anything looking like insurance/carrier/plan
        candidates = [t for t in tables if any(x in t for x in ['INSURANCE', 'PLAN', 'CARRIER', 'PAYER', 'POLICY', 'COVERAGE'])]
        print("Candidates:", candidates)
    except Exception as e: print(e)

if __name__ == "__main__":
    list_all_tables()
