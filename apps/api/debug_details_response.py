import requests
import json

def debug_details():
    era_id = '264792'
    url = f"http://localhost:8000/api/eras/{era_id}/details"
    
    try:
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            print("Successfully fetched data.")
            print(f"Bundles Count: {len(data.get('bundles', []))}")
            
            for b in data.get('bundles', []):
                print(f"Bundle {b['referenceId']} Claims: {len(b.get('claims', []))}")
                for c in b.get('claims', []):
                    # Check key fields used in frontend
                    print(f" - Date: {c.get('date')} | Status: {c.get('status')} | Adjustments: {c.get('adjustments')}")
                    
        else:
            print(f"Error: {res.status_code}")
            print(res.text)
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_details()
