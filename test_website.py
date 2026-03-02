import requests
from bs4 import BeautifulSoup

url = "https://www.stephensons.com/catering-crockery/steelite-crockery"
print(f"Testing: {url}")

try:
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}, timeout=10)
    print(f"Status: {r.status_code}")
    soup = BeautifulSoup(r.content, 'html.parser')
    
    # Check for products
    product_links = soup.select('li.product-item a.product-item-photo')
    print(f"Found {len(product_links)} products with 'li.product-item a.product-item-photo'")
    
    # Try alternative selectors
    alt1 = soup.select('a.product-item-photo')
    print(f"Found {len(alt1)} with 'a.product-item-photo'")
    
    alt2 = soup.select('.product-item')
    print(f"Found {len(alt2)} with '.product-item'")
    
    alt3 = soup.select('div[class*="product"]')
    print(f"Found {len(alt3)} with 'div[class*=\"product\"]'")
    
    # Check page structure
    print(f"\nPage HTML size: {len(r.content)} bytes")
    if 'product' in r.text.lower():
        print("Page contains 'product' text")
    if 'steelite' in r.text.lower():
        print("Page contains 'steelite' text")
        
except Exception as e:
    print(f"Error: {e}")
