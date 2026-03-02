import requests
from bs4 import BeautifulSoup

url = "https://www.webstaurantstore.com/steelite-distinction-monaco-vogue-12-oz-nouveau-bowl-case/5769001C372.html"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

r = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(r.content, 'html.parser')

# Test different title selectors
print("Testing title selectors:\n")

title1 = soup.select_one('h1[data-testid="product-detail-heading-title"]')
print(f"1. h1[data-testid='product-detail-heading-title']: {title1.get_text().strip() if title1 else 'NOT FOUND'}\n")

title2 = soup.select_one('h1.productDetailsHeading')
print(f"2. h1.productDetailsHeading: {title2.get_text().strip() if title2 else 'NOT FOUND'}\n")

title3 = soup.select_one('h1')
print(f"3. h1 (first): {title3.get_text().strip()[:80] if title3 else 'NOT FOUND'}\n")

title4 = soup.select_one('h1#page-header')
print(f"4. h1#page-header: {title4.get_text().strip() if title4 else 'NOT FOUND'}\n")

# Check all h1 tags
all_h1 = soup.find_all('h1')
print(f"\nTotal h1 tags found: {len(all_h1)}")
for i, h1 in enumerate(all_h1[:3], 1):
    print(f"  H1 #{i}: {h1.get_text().strip()[:80]}")
