from src.connection import get_connection
import logging

# Setup Logging to avoid clutter
logging.basicConfig(level=logging.ERROR)

try:
    conn = get_connection()
    cur = conn.cursor()
    print("Connected. Fetching PM_PRACTICE columns...")
    cur.execute("SELECT * FROM PM_PRACTICE LIMIT 1")
    col_names = sorted([desc[0] for desc in cur.description])
    print("\nColumns in PM_PRACTICE:")
    for c in col_names:
        print(f"- {c}")
    
    # Check for ISACTIVE variants
    candidates = [c for c in col_names if 'ACT' in c or 'STAT' in c]
    print(f"\nCandidates for Active Status: {candidates}")
    
except Exception as e:
    print(f"Error: {e}")
