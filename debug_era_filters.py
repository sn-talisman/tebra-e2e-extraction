import sys
import os
import asyncio

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'tebra-ux/backend'))

from app.api.eras import get_era_reports

async def test_filters():
    print("Testing get_era_reports with filters...")
    try:
        # Test 1: Hide Informational
        print("\n--- Test 1: Hide Informational ---")
        result = await get_era_reports(
            practice_guid='ee5ed349-d9dd-4bf5-81a5-aa503a261961',
            page=1,
            page_size=5,
            hide_informational=True
        )
        print(f"Success! Got {len(result)} rows.")
        
        # Test 2: Show Denials
        print("\n--- Test 2: Show Denials ---")
        result = await get_era_reports(
            practice_guid='ee5ed349-d9dd-4bf5-81a5-aa503a261961',
            page=1,
            page_size=5,
            show_denials=True
        )
        print(f"Success! Got {len(result)} rows.")

    except Exception as e:
        print(f"CRASHED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_filters())
