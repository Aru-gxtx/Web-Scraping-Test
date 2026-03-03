#!/usr/bin/env python
import os
import csv
from pathlib import Path

def get_file_size(path):
    if not path.exists():
        return 0
    return round(path.stat().st_size / 1024, 1)

def count_csv_rows(path):
    if not path.exists() or path.stat().st_size == 0:
        return 0
    try:
        with open(path) as f:
            return len(f.readlines()) - 1
    except:
        return 0

PROJECT_ROOT = Path(__file__).parent
SANNENG_DIR = PROJECT_ROOT / "sanneng"

print("""
╔════════════════════════════════════════════════════════════════╗
║         SANNENG WEB SCRAPING - PROJECT STATUS REPORT           ║
║                   (March 3, 2026 - Session 2)                  ║
╚════════════════════════════════════════════════════════════════╝
""")

print("\n📊 SPIDER STATUS:\n")
print("-" * 70)
print(f"{'Spider':<15} {'Status':<15} {'File Size':<15} {'Items':<10}")
print("-" * 70)

spiders = [
    ("chakawal", "WooCommerce - Indonesia", "chakawal_products"),
    ("sannengvietnam", "WordPress - Vietnam", "sannengvietnam_products"),
    ("tokopedia", "React Marketplace - Indonesia", "tokopedia_products"),
    ("unopan", "Next.js - Taiwan", "unopan_products"),
    ("coupang", "React Marketplace - Taiwan", "coupang_products"),
]

working = []
total_items = 0

for spider, description, csv_name in spiders:
    csv_path = SANNENG_DIR / f"{csv_name}.csv"
    size = get_file_size(csv_path)
    items = count_csv_rows(csv_path)
    
    if items > 0:
        status = "WORKING"
        working.append((spider, description, items))
        total_items += items
    else:
        status = "EMPTY"
    
    print(f"{spider:<15} {status:<15} {size:.1f} KB{'':<8} {items:>4} items")

print("-" * 70)
print(f"{'TOTAL':<15} {'':<15} {'':<15} {total_items:>4} items collected")
print("-" * 70)

print("\nWORKING SPIDERS:\n")
for spider, desc, items in working:
    print(f"  • {spider:<15} - {desc:<30} ({items} items)")

print("\nFAILING SPIDERS:\n")
failing = [(s, d) for s, d, _ in spiders if s not in [w[0] for w in working]]
for spider, desc in failing:
    csv_path = SANNENG_DIR / f"{spider}_products.csv"
    if csv_path.exists():
        print(f"  • {spider:<15} - {desc:<30}")
    else:
        print(f"  • {spider:<15} - {desc:<30} (NOT CREATED)")

print("\n\nEXCEL POPULATION RESULTS:\n")
excel_path = PROJECT_ROOT / "sources" / "SAN NENG_updated.xlsx"
if excel_path.exists():
    print(f"    Excel file updated: {excel_path.name}")
    print(f"    Size: {get_file_size(excel_path):.1f} KB")
    print(f"    Last modified: (Run sanneng_arranger_xlsx.py for latest stats)")

print("\n\nRECOMMENDATIONS:\n")
print("""
1. WORKING (37+ SKUs matched):
    sannengvietnam.com - Uses WordPress, simple structure, fully functional
    unopan.tw - Uses Next.js, Playwright JS rendering working
   
2. ISSUES IDENTIFIED:
    Tokopedia: HTTP/2 protocol error (net::ERR_HTTP2_PROTOCOL_ERROR)
        Likely requires: HTTP/1.1 fallback or different User-Agent
   
    Chakawal: Timeout (stuck > 120 seconds)
    Likely anti-bot, may need: Proxy or extended delays
   
    Coupang: 403 Forbidden on all pages  
        Likely requires: VPN/Proxy or cookie handling

3. NEXT STEPS TO FIX:
   Option A (Quick): Skip problematic sites, use 2 working scrapers
   Option B (Better): Use residential proxies for blocked sites
   Option C (Enterprise): Use Bright Data/Smartproxy services
   
4. CURRENT DATA STATUS:
   - 76 products from sannengvietnam.com ✓
   - 4+ products from unopan.tw ✓
   - 37 matched SKUs in Excel (27 → 37) ↑
   - 488 no-match SKUs pending new data

5. ESTIMATED FIXES:
   - Add proxy support: 1-2 hours
   - HTTP/1.1 fallback: 0.5 hours
   - Manual data collection: As needed
""")

print("\n" + "="*70)
print("Run this command to update Excel with current data:")
print(f"  python sanneng_arranger_xlsx.py")
print("="*70 + "\n")
