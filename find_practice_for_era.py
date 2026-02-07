import sys
import os
import asyncio

sys.path.append(os.path.join(os.getcwd(), 'tebra-ux/backend'))
from app.api.eras import get_db_cursor

def find_practice():
    print("Finding practice for ERA 272877...")
    era_id = '272877'
    
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT r.era_report_id, r.total_paid, p.name 
            FROM tebra.fin_era_report r
            JOIN tebra.cmn_practice p ON r.practice_guid::uuid = p.practice_guid
            WHERE r.era_report_id = %s
        """, (era_id,))
        row = cur.fetchone()
        
        if row:
            print(f"Found ERA {row[0]}: Total Paid ${row[1]}")
            print(f"Practice Name: '{row[2]}'")
        else:
            print("ERA not found in DB (unexpected).")

if __name__ == "__main__":
    find_practice()
