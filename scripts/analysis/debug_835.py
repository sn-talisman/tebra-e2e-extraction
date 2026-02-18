"""
Debug 835 content.
"""
import json

TARGET_FILENAME = "P05536D260228494U1932-26026B100008811300.RMT"

def debug_era():
    with open('eras_rejections_single_practice.json', 'r') as f:
        data = json.load(f)
        
    for item in data:
        if item.get('FILENAME') == TARGET_FILENAME:
            content = item.get('FILECONTENTS', '')
            print(f"Content Length: {len(content)}")
            print("First 500 chars raw repr:")
            print(repr(content[:500]))
            return

if __name__ == "__main__":
    debug_era()
