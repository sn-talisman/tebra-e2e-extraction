import sys
import os
import asyncio

sys.path.append(os.path.join(os.getcwd(), 'tebra-ux/backend'))
from app.api.eras import get_era_details, get_era_reports

async def check_paid_status():
    print("Checking status of Paid claims...")
    # Find an ERA with some payment
    eras = await get_era_reports(page=1, page_size=20, sort_by='total_paid', order='desc')
    paid_era = None
    for era in eras:
        if era['totalPaid'] > 0:
            paid_era = era
            break
            
    if not paid_era:
        print("No paid ERAs found.")
        return

    print(f"Checking Paid ERA: {paid_era['id']} (Paid: ${paid_era['totalPaid']})")
    details = await get_era_details(paid_era['id'])
    
    found_paid_line = False
    for b in details['bundles']:
        for claim in b['claims']:
            if claim['paid'] > 0:
                print(f"  Paid Claim {claim['claimId']}: ${claim['paid']} -> Status: {claim['status']}")
                if claim['status'] == 'Rejected':
                    print("  FAIL: Paid claim is marked as Rejected!")
                else:
                    found_paid_line = True
    
    if found_paid_line:
        print("Success: Found paid claims with non-Rejected status.")

    # Also check a true rejection to make sure we didn't break it
    print("\nChecking True Rejection...")
    # reuse the logic to find a rejected ERA
    eras = await get_era_reports(page=1, page_size=50, show_rejections=True)
    rejected_era = None
    for era in eras:
        if era['id'] == '278797': # The one we found earlier
             rejected_era = era
             break
    
    if rejected_era:
        print(f"Checking Rejected ERA: {rejected_era['id']}")
        details = await get_era_details(rejected_era['id'])
        for b in details['bundles']:
            for claim in b['claims']:
                if claim['paid'] == 0:
                     print(f"  Unpaid Claim {claim['claimId']}: ${claim['paid']} -> Status: {claim['status']}")

if __name__ == "__main__":
    asyncio.run(check_paid_status())
