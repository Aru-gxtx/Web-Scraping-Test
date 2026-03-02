#!/usr/bin/env python3
import subprocess
import os
import time
import glob

os.chdir('C:\\Users\\admin\\Documents\\GitHub\\Web-Scraping-Test')

# Delete old CSV files to get fresh results
for csv in glob.glob('steelite/*_products.csv'):
    try:
        os.remove(csv)
        print(f"Deleted old: {csv}")
    except:
        pass

# Spider configurations: (name, item_limit)
spiders = [
    ('wasserstrom', 20),
    ('steelitehome', 30),
    ('steelite_playwright', 10),  # utopia
    ('webstaurantstore_big', 20),
    ('stephensons', 15),
    ('kitchenrestock', 10),
    ('steelite_com', 15),
    ('us_steelite', 15),
    ('williamsfoodequipment', 15),
]

results = {}

for spider_name, limit in spiders:
    print(f"\n{'='*70}")
    print(f"Testing: {spider_name} (max {limit} items)")
    print(f"{'='*70}")
    
    os.chdir('steelite')
    cmd = ['py', '-m', 'scrapy', 'crawl', spider_name, 
           '-s', f'CLOSESPIDER_ITEMCOUNT={limit}',
           '-L', 'WARNING']
    
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    duration = time.time() - start
    os.chdir('..')
    
    # Check if CSV was created
    csv_file = f"steelite/{spider_name.replace('_playwright', '')}_products.csv"
    if spider_name == 'steelite_playwright':
        csv_file = "steelite/utopia_products.csv"
    
    csv_exists = os.path.exists(csv_file)
    
    if csv_exists:
        # Count rows
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                rows = sum(1 for line in f) - 1  # -1 for header
            results[spider_name] = {'status': 'SUCCESS', 'rows': rows, 'time': duration}
            print(f"✓ SUCCESS: {rows} products in {duration:.1f}s")
        except:
            results[spider_name] = {'status': 'ERROR', 'rows': 0, 'time': duration}
            print(f"✗ CSV exists but couldn't read")
    else:
        # Check output for errors
        if 'ERROR' in result.stderr or 'Exception' in result.stderr:
            results[spider_name] = {'status': 'FAILED', 'rows': 0, 'time': duration}
            print(f"✗ FAILED with errors in {duration:.1f}s")
        else:
            results[spider_name] = {'status': 'NO OUTPUT', 'rows': 0, 'time': duration}
            print(f"⚠ No CSV generated in {duration:.1f}s")
    
    time.sleep(1)

# Summary
print(f"\n{'='*70}")
print("FINAL SUMMARY")
print(f"{'='*70}")

working = [s for s, r in results.items() if r['status'] == 'SUCCESS']
failed = [s for s, r in results.items() if r['status'] != 'SUCCESS']

print(f"\n✓ WORKING ({len(working)}/9):")
for spider in working:
    print(f"  {spider:30} {results[spider]['rows']:3} products")

if failed:
    print(f"\n✗ NOT WORKING ({len(failed)}/9):")
    for spider in failed:
        print(f"  {spider:30} {results[spider]['status']}")

total_products = sum(r['rows'] for r in results.values())
print(f"\nTOTAL PRODUCTS: {total_products}")
