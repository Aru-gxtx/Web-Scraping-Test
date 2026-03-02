import requests
from bs4 import BeautifulSoup
import json

url = "https://www.webstaurantstore.com/vendor/steelite-international.html"
headers = {'UserAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

r = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(r.content, 'html.parser')

script_tag = soup.select_one('script[data-hypernova-key="BrandGroupPage"]')

if script_tag:
    script_text = script_tag.get_text()
    clean_json = script_text.strip()[4:-3]
    
    try:
        data = json.loads(clean_json)
        
        # Print the structure  
        print("JSON Keys:", list(data.keys())[:10])
        print()
        
        # Look for categories/groups related to Steelite
        if 'vendorGroups' in data:
            print(f"vendorGroups found: {len(data['vendorGroups'])} items")
            for i, group in enumerate(data['vendorGroups'][:3], 1):
                print(f"\nGroup {i}:")
                print(f"  Keys: {list(group.keys())}")
                if 'name' in group:
                    print(f"  Name: {group['name']}")
                if 'url' in group:
                    print(f"  URL: {group['url']}")
        
        if 'result' in data:
            print("\n'result' key found")
            if isinstance(data['result'], dict):
                print(f"  Keys in result: {list(data['result'].keys())[:10]}")
                
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
else:
    print("Script tag not found")
