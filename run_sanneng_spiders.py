#!/usr/bin/env python
import subprocess
import os
import sys
import time
from pathlib import Path

# Define directory paths
PROJECT_ROOT = Path(__file__).parent
SANNENG_DIR = PROJECT_ROOT / "sanneng"
ARRANGER_SCRIPT = PROJECT_ROOT / "sanneng_arranger_xlsx.py"
ADDON_SCRIPT = PROJECT_ROOT / "search_addon_enrichment.py"

# Define spider names and their output files
SPIDERS = [
    ("chakawal", "chakawal_products.csv"),
    ("sannengvietnam", "sannengvietnam_products.csv"),
    ("tokopedia", "tokopedia_products.csv"),
    ("unopan", "unopan_products.csv"),
    ("coupang", "coupang_products.csv"),
]

def run_command(cmd, cwd=None):
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=False,  # Show output in real-time
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError running command: {e}")
        return False
    except FileNotFoundError:
        print(f"\nCommand not found: {cmd[0]}")
        print("Make sure Scrapy is installed: pip install scrapy")
        return False

def check_prerequisites():
    print("Checking prerequisites...")
    
    # Check if scrapy is installed
    try:
        result = subprocess.run(
            [sys.executable, "-m", "scrapy", "version"],
            capture_output=True,
            text=True
        )
        print(f"Scrapy is installed: {result.stdout.strip()}")
    except FileNotFoundError:
        print("Scrapy is not installed. Please run: pip install scrapy")
        return False
    
    # Check if sanneng directory exists
    if not SANNENG_DIR.exists():
        print(f"Sanneng directory not found: {SANNENG_DIR}")
        return False
    print(f"Sanneng directory found: {SANNENG_DIR}")
    
    # Check if arranger script exists
    if not ARRANGER_SCRIPT.exists():
        print(f"Arranger script not found: {ARRANGER_SCRIPT}")
        return False
    print(f"✓ Arranger script found: {ARRANGER_SCRIPT}")

    # Check if addon script exists
    if not ADDON_SCRIPT.exists():
        print(f"SKU search add-on script not found: {ADDON_SCRIPT}")
        return False
    print(f"✓ SKU search add-on script found: {ADDON_SCRIPT}")
    
    return True

def run_spiders():
    print("\n" + "="*60)
    print("STARTING SPIDER EXECUTION")
    print("="*60)
    
    results = {}
    
    for spider_name, output_file in SPIDERS:
        start_time = time.time()
        
        # Run the spider
        cmd = [sys.executable, "-m", "scrapy", "crawl", spider_name, "-O", output_file]
        success = run_command(cmd, cwd=SANNENG_DIR)
        
        elapsed = time.time() - start_time
        results[spider_name] = {
            "success": success,
            "output": output_file,
            "time": elapsed
        }
        
        # Check if output file was created
        output_path = SANNENG_DIR / output_file
        if success and output_path.exists():
            file_size = output_path.stat().st_size
            print(f"✓ Spider '{spider_name}' completed in {elapsed:.1f}s")
            print(f"  Output: {output_file} ({file_size:,} bytes)")
        elif success:
            print(f"Spider '{spider_name}' ran but no output file found")
        else:
            print(f"Spider '{spider_name}' failed")
        
        # Small delay between spiders
        if spider_name != SPIDERS[-1][0]:
            time.sleep(2)
    
    return results

def run_arranger():
    print("\n" + "="*60)
    print("RUNNING EXCEL ARRANGER")
    print("="*60 + "\n")
    
    cmd = [sys.executable, str(ARRANGER_SCRIPT)]
    success = run_command(cmd, cwd=PROJECT_ROOT)
    
    if success:
        print("\n✓ Excel file populated successfully!")
        print("  Check: sources/SAN NENG_updated.xlsx")
    else:
        print("\nFailed to populate Excel file")
    
    return success


def run_search_addon():
    print("\n" + "="*60)
    print("RUNNING SKU SEARCH ADD-ON")
    print("="*60 + "\n")

    cmd = [sys.executable, str(ADDON_SCRIPT)]
    success = run_command(cmd, cwd=PROJECT_ROOT)

    if success:
        print("\n✓ SKU search add-on completed")
        print("  Check: sanneng/addon_search_products.csv")
    else:
        print("\nSKU search add-on failed")

    return success

def print_summary(spider_results, addon_success, arranger_success):
    print("\n" + "="*60)
    print("EXECUTION SUMMARY")
    print("="*60)
    
    print("\nSpiders:")
    total_time = 0
    for spider_name, result in spider_results.items():
        status = "SUCCESS" if result["success"] else "FAILED"
        print(f"  {spider_name:20} {status:12} ({result['time']:.1f}s)")
        total_time += result['time']
    
    print(f"\nTotal spider time: {total_time:.1f}s")
    
    print(f"\nExcel Arranger: {'SUCCESS' if arranger_success else 'FAILED'}")
    print(f"SKU Search Add-on: {'SUCCESS' if addon_success else 'FAILED'}")
    
    # Final status
    all_spiders_ok = all(r["success"] for r in spider_results.values())
    if all_spiders_ok and arranger_success and addon_success:
        print("\nALL OPERATIONS COMPLETED SUCCESSFULLY")
        return True
    else:
        print("\nSOME OPERATIONS FAILED - PLEASE REVIEW OUTPUT ABOVE")
        return False

def main():
    print("\n" + "="*60)
    print("SANNENG SPIDER RUNNER")
    print("="*60 + "\n")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\nPrerequisites check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Run all spiders
    spider_results = run_spiders()

    # Run search add-on enrichment
    addon_success = run_search_addon()

    arranger_success = run_arranger()
    
    # Print summary
    print_summary(spider_results, addon_success, arranger_success)
    
    # Exit with appropriate code
    all_success = all(r["success"] for r in spider_results.values())
    all_success = all_success and addon_success and arranger_success
    
    sys.exit(0 if all_success else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user")
        sys.exit(130)
