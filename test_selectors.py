import requests
from bs4 import BeautifulSoup

# Test webstaurantstore.com VENDOR page structure
url = "https://www.webstaurantstore.com/vendor/steelite-international.html"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print("Testing WebstaurantStore.com VENDOR PAGE selectors...")
r = requests.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(r.content, 'html.parser')

# Try different selectors
tests = [
    ('a[data-testid*="itemDescription"]', 'Item description testid'),
    ('a.description', 'Description class'),
    ('a[href*="/item/"]', 'Item href pattern'),
    ('div.ag-item a', 'AG item container'),
    ('a[id^="product_"]', 'Product ID prefix'),
    ('.product-box a', 'Product box links'),
    ('.product a', 'Product class links'),
    ('a[title*="Steelite"]', 'Steelite title attribute'),
]

for selector, desc in tests:
    found = soup.select(selector)
    print(f"  {desc:30} {len(found):3} matches")
    if found:
        print(f"    Sample: {found[0].get('href', 'NO HREF')[:80]}")

# Check specifically for product links
print(f"\nLooking for product patterns:")
product_links = [a.get('href') for a in soup.find_all('a') if a.get('href') and '/item/' in a.get('href')]
print(f"  /item/ pattern: {len(product_links)} links")
if product_links:
    print(f"  Sample: {product_links[0]}")
