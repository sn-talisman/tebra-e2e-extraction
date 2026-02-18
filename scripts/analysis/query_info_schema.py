from src.connection import get_connection

def query_info_schema():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Search for tables with INSURANCE in name
        q = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME LIKE '%INSURANCE%' 
           OR TABLE_NAME LIKE '%CARRIER%'
           OR TABLE_NAME LIKE '%PAYER%'
           OR TABLE_NAME LIKE '%PLAN%'
        """
        cursor.execute(q)
        tables = [row[0] for row in cursor.fetchall()]
        print("Found Tables via Info Schema:", tables)
        
    except Exception as e: print(e)

if __name__ == "__main__":
    query_info_schema()
