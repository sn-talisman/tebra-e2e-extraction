import sys
import os
import asyncio

sys.path.append(os.path.join(os.getcwd(), 'tebra-ux/backend'))
from app.api.eras import get_era_details, get_db_cursor

async def inspect_era_272877():
    print("Inspecting ERA 272877...")
    era_id = '272877'
    
    # 1. Check Raw DB rows
    print("\n[Raw DB Rows]")
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                cl.tebra_claim_id, 
                cl.paid_amount, 
                cl.claim_status, 
                cl.payer_status
            FROM tebra.fin_era_bundle b
            JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
            WHERE b.era_report_id = %s
        """, (era_id,))
        rows = cur.fetchall()
        for row in rows:
            print(f"Claim {row[0]}: Paid={row[1]}, Status='{row[2]}', PayerStatus='{row[3]}'")

    # 2. Check Python Processing
    print("\n[Python Processed Details]")
    details = await get_era_details(era_id)
    
    if "summary" in details:
        s = details['summary']
        print(f"Summary: Paid={s.get('paid')}, Rejected={s.get('rejected')}, Denied={s.get('denied')}")
    else:
        print("Summary: MISSING")

    for b in details['bundles']:
        for claim in b['claims']:
            print(f"Claim {claim['claimId']}: Paid={claim['paid']}, Status='{claim['status']}', PrevReject={claim.get('previouslyRejected')}")

if __name__ == "__main__":
    asyncio.run(inspect_era_272877())
