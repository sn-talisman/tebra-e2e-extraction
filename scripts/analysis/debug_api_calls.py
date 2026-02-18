import requests
import json

BASE_URL = "http://localhost:8000/api"

def debug_api():
    print("--- Debugging API ---")
    
    # 1. Fetch Practices
    try:
        print("\n1. GET /practices/list")
        resp = requests.get(f"{BASE_URL}/practices/list")
        resp.raise_for_status()
        practices = resp.json()
        print(f"Status: {resp.status_code}")
        print(f"Count: {len(practices)}")
        
        target_practice = None
        for p in practices:
            print(f" - {p.get('name')} (GUID: {p.get('locationGuid')})")
            if "PERFORMANCE" in p.get('name', '').upper():
                target_practice = p
        
    except Exception as e:
        print(f"FAIL: {e}")
        return

    # 2. Fetch ERAs for Target Practice
    if target_practice:
        guid = target_practice.get('locationGuid')
        print(f"\n2. GET /eras/list?practice_guid={guid}")
        try:
            resp = requests.get(f"{BASE_URL}/eras/list", params={
                "practice_guid": guid,
                "page": 1,
                "page_size": 20
            })
            resp.raise_for_status()
            eras = resp.json()
            print(f"Status: {resp.status_code}")
            print(f"Count: {len(eras)}")
            if len(eras) > 0:
                print("First ERA sample:")
                print(json.dumps(eras[0], indent=2))
            else:
                print("Response is empty list []")
        except Exception as e:
            print(f"FAIL: {e}")
    else:
        print("\nSkipping ERA fetch: Target practice not found in list.")

if __name__ == "__main__":
    debug_api()
