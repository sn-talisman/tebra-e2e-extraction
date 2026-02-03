from src.connection import get_connection

def check_schema():
    conn = get_connection()
    cursor = conn.cursor()
    print("Columns in PM_ENCOUNTERPROCEDURE:")
    cursor.execute("DESCRIBE TABLE PM_ENCOUNTERPROCEDURE")
    cols = [row[0] for row in cursor.fetchall()]
    print(cols)

if __name__ == "__main__":
    check_schema()
