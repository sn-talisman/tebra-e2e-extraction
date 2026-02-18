from src.connection import get_connection

def check_id_new():
    conn = get_connection()
    cursor = conn.cursor()
    
    val = 602208
    print(f"Checking {val} in PM_CLAIM...")
    
    q1 = f"SELECT * FROM PM_CLAIM WHERE CLAIMID = {val}"
    cursor.execute(q1)
    if cursor.fetchone():
        print(f"FOUND as CLAIMID!")
    else:
        print(f"NOT found as CLAIMID.")
        
    conn.close()

if __name__ == "__main__":
    check_id_new()
