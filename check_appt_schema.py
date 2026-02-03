from src.connection import get_connection

def check_appt_schema():
    conn = get_connection()
    cursor = conn.cursor()
    print("--- PM_APPOINTMENT ---")
    try:
        cursor.execute("DESCRIBE TABLE PM_APPOINTMENT")
        cols = [row[0] for row in cursor.fetchall()]
        print(cols)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_appt_schema()
