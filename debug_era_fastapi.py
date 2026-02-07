import sys
import os
import asyncio

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'tebra-ux/backend'))

from app.api.eras import get_era_reports

async def test_endpoint():
    print("Testing get_era_reports...")
    try:
        # Mimic the browser request
        result = await get_era_reports(
            practice_guid='ee5ed349-d9dd-4bf5-81a5-aa503a261961',
            page=1,
            page_size=5,
            sort_by='date',
            order='desc'
        )
        print("Success!")
        print(f"Got {len(result)} rows.")
        for row in result:
            print(row)
    except Exception as e:
        print(f"CRASHED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_endpoint())
