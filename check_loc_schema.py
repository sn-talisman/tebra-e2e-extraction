from src.connection import get_connection

def check_loc_schema():
    conn = get_connection()
    cursor = conn.cursor()
    print("--- PM_SERVICELOCATION ---")
    try:
        cursor.execute("DESCRIBE TABLE PM_SERVICELOCATION")
        cols = [row[0] for row in cursor.fetchall()]
        print(cols)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_loc_schema()
