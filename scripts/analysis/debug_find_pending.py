import sys
import os
import asyncio

sys.path.append(os.path.join(os.getcwd(), 'tebra-ux/backend'))
from app.api.eras import get_era_details

async def verify_pending_fix():
    print("Verifying fix for 'Pending' status on ERA 280508...")
    era_id = '280508'
    
    details = await get_era_details(era_id)
    
    pending_count = 0
    denied_count = 0
    rejected_count = 0
    
    for b in details['bundles']:
        for claim in b['claims']:
            status = claim['status']
            paid = claim['paid']
            print(f"Claim {claim['claimId']}: Paid=${paid}, Status='{status}'")
            
            if status == 'Pending':
                pending_count += 1
            elif status == 'Denied':
                denied_count += 1
            elif status == 'Rejected':
                rejected_count += 1

    print(f"\nSummary for ERA {era_id}:")
    print(f"  Pending: {pending_count}")
    print(f"  Denied: {denied_count}")
    print(f"  Rejected: {rejected_count}")
    
    if pending_count == 0 and denied_count > 0:
        print("\nSUCCESS: No 'Pending' claims found. They were mapped to 'Denied'.")
    else:
        print("\nFAILURE: 'Pending' status still exists or mapping failed.")

if __name__ == "__main__":
    asyncio.run(verify_pending_fix())
