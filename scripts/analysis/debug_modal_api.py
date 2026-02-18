import requests
import json

BASE_URL = "http://localhost:8000/api"
ERA_ID = "280269"

def debug_modal():
    print(f"--- Debugging Modal API for ERA {ERA_ID} ---")
    try:
        url = f"{BASE_URL}/eras/{ERA_ID}/details"
        print(f"GET {url}")
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        print(f"Status: {resp.status_code}")
        print("Header:")
        print(f"  Payer: {data.get('payer')}")
        print(f"  Check: {data.get('checkNumber')}")
        
        bundles = data.get('bundles', [])
        print(f"Bundles: {len(bundles)}")
        if bundles:
            print("First Bundle Sample:")
            print(json.dumps(bundles[0], indent=2))
            
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    debug_modal()
