#!/usr/bin/env python3
import subprocess
import os
import time

def run_spider(spider_name):
    print(f"\n{'='*70}")
    print(f"Running: {spider_name}")
    print(f"{'='*70}")
    
    os.chdir('steelite')
    cmd = ['py', '-m', 'scrapy', 'crawl', spider_name, '-L', 'INFO']
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.chdir('..')
    
    # Print last 10 lines of output
    lines = result.stdout.split('\n')
    for line in lines[-15:]:
        if line.strip():
            print(line)
    
    return result.returncode == 0

# Run all working spiders
working_spiders = ['wasserstrom', 'steelitehome', 'steelite_playwright']

results = {}
for spider in working_spiders:
    try:
        results[spider] = run_spider(spider)
        time.sleep(2)
    except Exception as e:
        print(f"ERROR: {e}")
        results[spider] = False

# Merge and populate
print(f"\n{'='*70}")
print("MERGING AND POPULATING EXCEL")
print(f"{'='*70}\n")

os.chdir('C:\\Users\\admin\\Documents\\GitHub\\Web-Scraping-Test')
result = subprocess.run(['py', 'arranger_xlsx.py'], capture_output=True, text=True)

# Show output
for line in result.stdout.split('\n'):
    if 'Populated' in line or 'Total' in line or 'Saved' in line:
        print(line)

print(f"\n{'='*70}")
print("SUMMARY")
print(f"{'='*70}\n")
for spider, success in results.items():
    status = "✓ OK" if success else "✗ FAILED"
    print(f"  {spider:25} {status}")
