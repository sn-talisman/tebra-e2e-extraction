from src.connection import get_connection

def inspect_practice_columns():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT TOP 1 * FROM PM_PRACTICE")
        col_names = [desc[0] for desc in cur.description]
        print("PM_PRACTICE Columns:")
        for c in sorted(col_names):
            print(f"- {c}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_practice_columns()
