from src.connection import get_connection

def check_id(val):
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"Checking {val} in PM_CLAIM...")
    
    # 1. Check as CLAIMID
    q1 = f"SELECT * FROM PM_CLAIM WHERE CLAIMID = {val}"
    cursor.execute(q1)
    if cursor.fetchone():
        print(f"FOUND as CLAIMID!")
    else:
        print(f"NOT found as CLAIMID.")
        
    # 2. Check as ENCOUNTERPROCEDUREID
    q2 = f"SELECT * FROM PM_CLAIM WHERE ENCOUNTERPROCEDUREID = {val}"
    cursor.execute(q2)
    if cursor.fetchone():
        print(f"FOUND as ENCOUNTERPROCEDUREID!")
    else:
        print(f"NOT found as ENCOUNTERPROCEDUREID.")

    conn.close()

if __name__ == "__main__":
    check_id(600408)
