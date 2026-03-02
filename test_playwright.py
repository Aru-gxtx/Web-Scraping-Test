from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url = "https://www.webstaurantstore.com/vendor/steelite-international.html"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until="networkidle", timeout=60000)
    
    # Wait a bit for JavaScript to load
    page.wait_for_timeout(3000)
    
    content = page.content()
    browser.close()

soup = BeautifulSoup(content, 'html.parser')

# Test various selectors
tests = [
    ("Product divs: 'div.ag-item'", soup.select('div.ag-item')),
    ("Product divs: 'div[class*=\"product\"]'", soup.select('div[class*="product"]')),
    ("Product links: 'a[href*=\"/item/\"]'", soup.select('a[href*="/item/"]')),
    ("Description links: 'a.description'", soup.select('a.description')),
    ("All product-like classes", soup.find_all(class_=lambda x: x and 'product' in str(x).lower())[:5]),
]

print(f"\n=== Playwright Rendered Page Analysis ===\n")
for desc, result in tests:
    print(f"{desc}: {len(result)} matches")
    if result and len(result) > 0:
        print(f"  First match: {result[0]}")
        print()

# Find all unique class names containing "product"
all_classes = set()
for tag in soup.find_all(class_=True):
    for cls in tag.get('class', []):
        if 'product' in cls.lower() or 'item' in cls.lower():
            all_classes.add(cls)

print("\n=== Classes containing 'product' or 'item': ===")
for cls in sorted(all_classes)[:20]:
    print(f"  {cls}")

# Find any links
all_links = soup.find_all('a', href=True)
print(f"\n=== Total links found: {len(all_links)} ===")
item_links = [a['href'] for a in all_links if '/item/' in a['href']]
print(f"Links containing '/item/': {len(item_links)}")
if item_links:
    print(f"  First 3: {item_links[:3]}")
