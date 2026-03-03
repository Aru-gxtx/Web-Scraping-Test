#!/usr/bin/env python
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
SANNENG_DIR = PROJECT_ROOT / "sanneng"
PYTHON_EXE = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

SPIDERS_TO_DEBUG = {
    "chakawal": "WooCommerce site - Indonesian provider",
    "tokopedia": "React-based marketplace - Indonesian",
    "coupang": "React-based marketplace - Taiwanese",
}

def run_debug_spider(spider_name, description):
    print(f"\n{'='*70}")
    print(f"DEBUGGING: {spider_name.upper()} - {description}")
    print(f"{'='*70}\n")
    
    cmd = [
        str(PYTHON_EXE),
        "-m", "scrapy",
        "crawl", spider_name,
        "-L", "INFO",
        "-o", f"{spider_name}_debug.csv"
    ]
    
    result = subprocess.run(
        cmd,
        cwd=str(SANNENG_DIR),
        capture_output=True,
        text=True,
        timeout=120
    )
    
    # Print all output
    if result.stderr:
        lines = result.stderr.split('\n')
        # Find key diagnostics
        for i, line in enumerate(lines):
            if any(x in line for x in ['Found', 'Scraped', 'Error', 'ERROR', 'parse', 'parse_product', 'CSS', 'selector']):
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                for l in lines[start:end]:
                    if l.strip():
                        print(l)
                print()
    
    # Check output
    output_file = SANNENG_DIR / f"{spider_name}_debug.csv"
    if output_file.exists():
        size = output_file.stat().st_size
        print(f"\nOutput file size: {size} bytes")
        if size > 50:  # Has header + data
            with open(output_file) as f:
                lines = f.readlines()
                print(f"Total lines: {len(lines)}")
                print("First few lines (header + first 2 rows):")
                for line in lines[:3]:
                    print(line.rstrip()[:120] + ("..." if len(line) > 120 else ""))
    else:
        print("\nNo output file created!")

if __name__ == "__main__":
    for spider, desc in SPIDERS_TO_DEBUG.items():
        try:
            run_debug_spider(spider, desc)
        except subprocess.TimeoutExpired:
            print(f"✗ {spider} timed out after 120 seconds")
        except Exception as e:
            print(f"✗ {spider} error: {e}")
