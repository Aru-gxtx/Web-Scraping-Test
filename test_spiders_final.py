#!/usr/bin/env python
import subprocess
import os
import sys
from pathlib import Path

# Setup
PROJECT_ROOT = Path(__file__).parent
SANNENG_DIR = PROJECT_ROOT / "sanneng"
PYTHON_EXE = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

# Spider names
SPIDERS = ["chakawal", "sannengvietnam", "tokopedia", "unopan", "coupang"]

def run_spider(spider_name):
    output_file = f"{spider_name}_products.csv"
    cmd = [
        str(PYTHON_EXE),
        "-m", "scrapy",
        "crawl", spider_name,
        "-O", output_file
    ]
    
    print(f"\n{'='*70}")
    print(f"Running spider: {spider_name.upper()}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(SANNENG_DIR),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Print last 30 lines of output
        stderr_lines = result.stderr.split('\n')[-30:]
        print("\nLast 30 lines of output:")
        for line in stderr_lines:
            if line.strip():
                print(line)
        
        #  Check output file
        output_path = SANNENG_DIR / output_file
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"\nOutput file created: {output_file} ({file_size} bytes)")
            return output_file, file_size
        else:
            print(f"\nOutput file not created!")
            return None, 0
            
    except subprocess.TimeoutExpired:
        print(f"\nSpider timed out after 300 seconds!")
        return None, 0
    except Exception as e:
        print(f"\n✗ Error running spider: {e}")
        return None, 0

if __name__ == "__main__":
    os.chdir(PROJECT_ROOT)
    
    print(f"Python executable: {PYTHON_EXE}")
    print(f"Sanneng directory: {SANNENG_DIR}")
    print(f"Working directory: {os.getcwd()}")
    
    results = {}
    for spider in SPIDERS:
        output_file, size = run_spider(spider)
        results[spider] = (output_file, size)
    
    # Summary
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    for spider, (output_file, size) in results.items():
        status = "✓" if size > 0 else "✗"
        print(f"{status} {spider:15} - {size:8} bytes")
    
    # Check total data collected
    total_size = sum(size for _, size in results.values())
    print(f"\nTotal data collected: {total_size} bytes")
    if total_size > 0:
        print("\nSpiders completed! Now run: python sanneng_arranger_xlsx.py")
