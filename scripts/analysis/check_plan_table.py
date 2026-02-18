from src.connection import get_connection

def check_plan_table():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DESCRIBE TABLE PM_INSURANCECOMPANYPLAN")
        cols = [row[0] for row in cursor.fetchall()]
        print("PM_INSURANCECOMPANYPLAN:", cols)
    except Exception as e: print(e)

if __name__ == "__main__":
    check_plan_table()
