from src.connection import get_connection

def inspect_claim_columns():
    conn = get_connection()
    cur = conn.cursor()
    # Using SQL to get one row and print keys/descriptions or query info schema for PM_CLAIM
    try:
        cur.execute("SELECT TOP 1 * FROM PM_CLAIM")
        col_names = [desc[0] for desc in cur.description]
        print("PM_CLAIM Columns:")
        for c in sorted(col_names):
            print(f"- {c}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_claim_columns()
