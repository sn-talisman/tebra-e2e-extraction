from src.connection import get_connection

def research_insurance():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Check PM_CLAIM for Insurance Keys
    print("\n--- PM_CLAIM Columns ---")
    try:
        cursor.execute("DESCRIBE TABLE PM_CLAIM")
        cols = [row[0] for row in cursor.fetchall() if 'INSURANCE' in row[0] or 'PLAN' in row[0] or 'CARRIER' in row[0]]
        print(cols)
    except Exception as e: print(e)

    # 2. Check PM_ENCOUNTER for Insurance Keys
    print("\n--- PM_ENCOUNTER Columns ---")
    try:
        cursor.execute("DESCRIBE TABLE PM_ENCOUNTER")
        cols = [row[0] for row in cursor.fetchall() if 'INSURANCE' in row[0] or 'PLAN' in row[0] or 'CARRIER' in row[0]]
        print(cols)
    except Exception as e: print(e)

    # 3. List Insurance Tables
    print("\n--- Insurance Tables ---")
    try:
        cursor.execute("SHOW TABLES LIKE 'PM_%INSURANCE%'")
        tables = [row[1] for row in cursor.fetchall()]
        print(tables)
    except Exception as e: print(e)
    
    # 4. Describe PM_INSURANCEPLAN if it exists
    print("\n--- PM_INSURANCEPLAN Schema ---")
    try:
        cursor.execute("DESCRIBE TABLE PM_INSURANCEPLAN")
        cols = [row[0] for row in cursor.fetchall()]
        print(cols)
    except Exception as e: print(e)

if __name__ == "__main__":
    research_insurance()
