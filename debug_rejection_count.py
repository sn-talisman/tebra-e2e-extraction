import sys
import os
import asyncio

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'tebra-ux/backend'))

from app.api.eras import get_era_reports, get_era_details

async def compare_counts():
    print("Scanning for Paid ERAs with Mismatched Counts...")
    
    # 1. Get all paid ERAs
    reports = await get_era_reports(page=1, page_size=100, sort_by='total_paid', order='desc')
    
    mismatch_found = False
    for r in reports:
        if r['totalPaid'] > 0 and (r['rejectedCount'] > 0 or r['deniedCount'] > 0):
            print(f"\nChecking Paid ERA {r['id']} (Paid: ${r['totalPaid']})")
            print(f"  Table Rejected: {r['rejectedCount']}, Table Denied: {r['deniedCount']}")
            
            # 2. Get Details and count actual rejections/denials based on new logic
            details = await get_era_details(r['id'])
            
            modal_rejected = 0
            modal_denied = 0
            for b in details['bundles']:
                for claim in b['claims']:
                    if claim['status'] == 'Rejected':
                        modal_rejected += 1
                    elif claim['status'] == 'Denied':
                        modal_denied += 1
            
            print(f"  Modal Rejected: {modal_rejected}, Modal Denied: {modal_denied}")
            
            if r['rejectedCount'] != modal_rejected or r['deniedCount'] != modal_denied:
                print("  !!! MISMATCH DETECTED !!!")
                mismatch_found = True
            else:
                print("  Counts match.")

    if not mismatch_found:
        print("\nNo mismatches found in top 100 paid ERAs.")

if __name__ == "__main__":
    asyncio.run(compare_counts())
