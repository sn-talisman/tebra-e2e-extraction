from extract_batch_optimized import extract_batch, get_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target IDs from report: 713793, 713794, 713795, 713796
TARGET_IDS = ['713793', '713794', '713795', '713796']

def debug_diag_lookup():
    conn = get_connection()
    cur = conn.cursor()
    ids_str = ", ".join([f"'{d}'" for d in TARGET_IDS])
    
    print(f"--- Querying ICD10 Table for {ids_str} ---")
    cur.execute(f"SELECT ICD10DIAGNOSISCODEDICTIONARYID, OFFICIALNAME FROM PM_ICD10DIAGNOSISCODEDICTIONARY WHERE ICD10DIAGNOSISCODEDICTIONARYID IN ({ids_str})")
    rows = cur.fetchall()
    print(f"ICD10 Rows Found: {len(rows)}")
    for r in rows: print(r)

    print(f"\n--- Querying Legacy Table (PM_DIAGNOSISCODEDICTIONARY) ---")
    # Try the other table
    cur.execute(f"SELECT DIAGNOSISCODEDICTIONARYID, OFFICIALNAME FROM PM_DIAGNOSISCODEDICTIONARY WHERE DIAGNOSISCODEDICTIONARYID IN ({ids_str})")
    rows = cur.fetchall()
    print(f"Legacy Rows Found: {len(rows)}")
    for r in rows: print(r)
    
    conn.close()

if __name__ == "__main__":
    debug_diag_lookup()
