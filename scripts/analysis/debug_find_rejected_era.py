import sys
import os
import asyncio

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'tebra-ux/backend'))

from app.api.eras import get_era_reports, get_era_details

async def find_and_inspect_rejected():
    print("Searching for ERA with rejections...")
    # Get list, sort by rejected count descending to find one quickly
    eras = await get_era_reports(page=1, page_size=50, show_rejections=True)
    
    rejected_era = None
    for era in eras:
        if era['rejectedCount'] > 0:
            rejected_era = era
            break
            
    if not rejected_era:
        print("No ERAs with rejections found.")
        return

    era_id = rejected_era['id']
    print(f"Found Rejected ERA: {era_id} (Rejections: {rejected_era['rejectedCount']})")
    
    print(f"\nFetching details for {era_id}...")
    details = await get_era_details(era_id)
    
    print(f"Bundles: {len(details['bundles'])}")
    for b in details['bundles']:
        for claim in b['claims']:
            print(f"  Claim ID: {claim['claimId']}")
            print(f"    Status (API): {claim['status']}")
            print(f"    Adjustments: {claim['adjustments']}")
            # We want to see if raw rows had different statuses, but we can't see raw rows here easily 
            # without modifying code or trusting the hypothesis. 
            # But seeing 'Processed' here when we expect 'Rejected' would confirm the user issue.

if __name__ == "__main__":
    asyncio.run(find_and_inspect_rejected())
