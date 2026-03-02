#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

# Map spider names to their output CSV files
SPIDERS_TO_TEST = {
    "steelite_playwright": "utopia_products.csv",
    "webstaurantstore_vendor": "webstaurantstore_vendor_products.csv",
    "stephensons": "stephensons_products.csv",
    "us_steelite": "us_steelite_products.csv",
    "williamsfoodequipment": "williamsfoodequipment_products.csv",
}

print("=" * 60)
print("Testing Spiders Individually")
print("=" * 60)

venv_python = Path(".venv/Scripts/python.exe")

for spider_name, csv_filename in SPIDERS_TO_TEST.items():
    print(f"\n[Testing: {spider_name}]")
    print("-" * 40)
    
    csv_path = Path("steelite") / csv_filename
    if csv_path.exists():
        csv_path.unlink()  # Delete old CSV
        print(f"  Cleared old: {csv_filename}")
    
    # Run spider with limited items for testing
    cmd = [
        str(venv_python),
        "-m", "scrapy", "crawl", spider_name,
        "-s", "CLOSESPIDER_ITEMCOUNT=5",  # Stop after 5 items
        "-s", "LOG_LEVEL=INFO"
    ]
    
    print(f"  Running: scrapy crawl {spider_name}")
    result = subprocess.run(
        cmd,
        cwd="steelite",
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if csv_path.exists():
        with open(csv_path) as f:
            lines = len(f.readlines())
        print(f"  ✓ SUCCESS: {lines-1} products scraped")
    else:
        print(f"  ✗ FAILED: No output CSV created")
        # Show last few lines of error
        if result.stderr:
            errors = [line for line in result.stderr.split('\n') if 'ERROR' in line or 'Traceback' in line]
            if errors:
                print(f"  Errors: {errors[:3]}")

print("\n" + "=" * 60)
print("Testing Complete")
print("=" * 60)
