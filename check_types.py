from src.connection import get_connection

def check_types():
    conn = get_connection()
    cursor = conn.cursor()
    print("Checking Report Types...")
    try:
        cursor.execute("SELECT DISTINCT CLEARINGHOUSERESPONSEREPORTTYPENAME FROM PM_CLEARINGHOUSERESPONSE")
        for r in cursor.fetchall():
            print(f"- {r[0]}")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()

if __name__ == "__main__":
    check_types()
