#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import glob

# Add steelite to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'steelite'))

def get_python_exe():
    venv_path = os.path.join(os.path.dirname(__file__), '.venv', 'Scripts', 'python.exe')
    if os.path.exists(venv_path):
        return venv_path
    return sys.executable

def run_spider(spider_name):
    print(f"\n{'='*60}")
    print(f"Running spider: {spider_name}")
    print(f"{'='*60}")
    
    cmd = [
        get_python_exe(), '-m', 'scrapy', 'crawl', spider_name,
        '-L', 'INFO'
    ]
    
    os.chdir(os.path.join(os.path.dirname(__file__), 'steelite'))
    result = subprocess.run(cmd, capture_output=False)
    os.chdir(os.path.dirname(__file__))
    
    return result.returncode == 0

def main():
    print("\n" + "="*60)
    print("STEELITE PRODUCT SCRAPER - WORKING SPIDERS ONLY")
    print("="*60)
    
    # List of working spiders (tested and verified)
    working_spiders = [
        'steelitehome',       # 327 products
        'wasserstrom',         # 100 products  
        'stephensons',         # ~31 products
        'steelite_playwright', # 19 products (utopia/shelf)
    ]
    
    # Run each spider
    results = {}
    for spider in working_spiders:
        try:
            results[spider] = run_spider(spider)
            time.sleep(2)  # Small delay between spiders
        except Exception as e:
            print(f"Error running {spider}: {e}")
            results[spider] = False
    
    # Now merge CSVs and populate Excel
    print(f"\n{'='*60}")
    print("MERGING CSV FILES AND POPULATING EXCEL")
    print(f"{'='*60}\n")
    
    os.chdir(os.path.join(os.path.dirname(__file__), 'steelite'))
    cmd = [get_python_exe(), '../arranger_xlsx.py']
    subprocess.run(cmd)
    os.chdir(os.path.dirname(__file__))
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for spider, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {spider:25} {status}")

if __name__ == '__main__':
    main()
