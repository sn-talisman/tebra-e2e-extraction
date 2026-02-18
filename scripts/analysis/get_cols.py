from src.connection import get_connection

def describe():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM PM_CLAIM LIMIT 1")
        print("Columns:")
        for d in cur.description:
            print(f"- {d[0]}")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()

if __name__ == "__main__":
    describe()
