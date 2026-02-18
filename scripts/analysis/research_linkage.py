from src.connection import get_connection

TARGET_GUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'

# ERA Data
ERA_FULL_ID = '388506Z43267'
USER_HINT_ID = '598543'

def research_linkage():
    conn = get_connection()
    cursor = conn.cursor()
    
    # We will search these tables
    tables = ['PM_CLAIM', 'PM_ENCOUNTERPROCEDURE', 'PM_PAYMENT']
    
    # Search items
    search_values = [USER_HINT_ID, ERA_FULL_ID]
    # Add ERA substring (first 6 chars) just in case
    if len(ERA_FULL_ID) > 6:
        search_values.append(ERA_FULL_ID[:6])
        
    print(f"Searching for values: {search_values}")

    for t in tables:
        print(f"\n--- Analyzing {t} ---")
        try:
            cursor.execute(f"DESCRIBE TABLE {t}")
            rows = cursor.fetchall()
            
            # rows: [name, type, ...]
            # Filter for columns that might hold an ID
            target_cols = []
            for r in rows:
                col_name = r[0]
                col_type = r[1]
                
                # Heuristic: Look for ID columns or String columns
                # Tebra IDs are often NUMBER, but External IDs are VARCHAR.
                is_id_col = 'ID' in col_name or 'REF' in col_name or 'NUM' in col_name
                is_string = 'VARCHAR' in col_type or 'STRING' in col_type
                is_number = 'NUMBER' in col_type
                
                if is_id_col:
                    target_cols.append(col_name)
            
            print(f"Scanning {len(target_cols)} relevant columns in {t}...")
            
            # Construct a search query (OR clauses)
            conditions = []
            for col in target_cols:
                for val in search_values:
                    # If column is number, only search if val is numeric
                    # We don't have column type map handy in this loop efficiently without re-looping or dict.
                    # Let's just assume we cast/quote safely.
                    # Safest is to treat everything as string comparison if possible, or try/catch.
                    # Snowflake allows '123' = NUMBER_COL usually.
                    conditions.append(f"CAST({col} AS VARCHAR) = '{val}'")
            
            if not conditions:
                continue
                
            # Chunking conditions to avoid query length limits if too many
            # But here we have few values.
            
            query = f"SELECT * FROM {t} WHERE PRACTICEGUID = '{TARGET_GUID}' AND ({' OR '.join(conditions)}) LIMIT 5"
            
            cursor.execute(query)
            matches = cursor.fetchall()
            
            if matches:
                print(f"!!! MATCH FOUND IN {t} !!!")
                # Print column headers
                headers = [r[0] for r in rows]
                
                for row in matches:
                    # Zip and print non-nulls
                    data = dict(zip(headers, row))
                    # Print useful info
                    print(f"Match Row: {data.get('CLAIMID') or data.get('PAYMENTID') or 'UnknownID'}")
                    print(f"  PatientGUID: {data.get('PATIENTGUID')}")
                    print(f"  EncounterGUID: {data.get('ENCOUNTERGUID') or data.get('SOURCEENCOUNTERGUID')}")
                    # Print identifying columns
                    for k,v in data.items():
                        if str(v) in search_values:
                            print(f"  MATCHED COLUMN: {k} = {v}")
            else:
                print("No matches found.")
                
        except Exception as e:
            print(f"Error checking {t}: {e}")

if __name__ == "__main__":
    research_linkage()
