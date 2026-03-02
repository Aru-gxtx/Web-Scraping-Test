#!/usr/bin/env python3
import subprocess
import sys
import os
from pathlib import Path
import time
import platform

# Spiders to run in order - All 9 website scrapers
SPIDERS = [
    "wasserstrom",                  # Wasserstrom.com - WORKING (100+ products)
    "steelitehome",                 # SteeliteHome.com - WORKING (325+ products)
    "steelite_playwright",          # Steelite-utopia.com - WORKING (19+ products)
    "webstaurantstore_big",         # WebstaurantStore search - FIXED
    "stephensons",                  # Stephensons.com - FIXED
    "kitchenrestock",               # KitchenRestock.com - FIXED
    "steelite_com",                 # Steelite.com main site
    "us_steelite",                  # us.steelite.com
    "williamsfoodequipment",        # WilliamsFoodEquipment.com
]

# Determine if we should use colors (not on Windows)
USE_COLORS = platform.system() != "Windows"

# Colors for output
class Colors:
    HEADER = '\033[95m' if USE_COLORS else ''
    OKBLUE = '\033[94m' if USE_COLORS else ''
    OKCYAN = '\033[96m' if USE_COLORS else ''
    OKGREEN = '\033[92m' if USE_COLORS else ''
    WARNING = '\033[93m' if USE_COLORS else ''
    FAIL = '\033[91m' if USE_COLORS else ''
    ENDC = '\033[0m' if USE_COLORS else ''
    BOLD = '\033[1m' if USE_COLORS else ''
    UNDERLINE = '\033[4m' if USE_COLORS else ''


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text):
    print(f"{Colors.OKGREEN}[SUCCESS] {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.OKCYAN}[INFO] {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.WARNING}[WARNING] {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.FAIL}[ERROR] {text}{Colors.ENDC}")


def run_spider(spider_name):
    print_info(f"Starting spider: {spider_name}")
    
    try:
        import sys
        from scrapy.cmdline import execute
        
        # Save original argv and cwd
        original_argv = sys.argv
        original_cwd = os.getcwd()
        
        try:
            # Change to steelite directory
            os.chdir("steelite")
            
            # Set up scrapy command
            sys.argv = ["scrapy", "crawl", spider_name]
            
            # Execute scrapy
            result = execute()
            
            os.chdir(original_cwd)
            sys.argv = original_argv
            
            if result is None or result == 0:
                print_success(f"Spider '{spider_name}' completed successfully")
                return True
            else:
                print_error(f"Spider '{spider_name}' returned code {result}")
                return False
                
        except SystemExit as e:
            os.chdir(original_cwd)
            sys.argv = original_argv
            # SystemExit with 0 = success
            if e.code == 0 or e.code is None:
                print_success(f"Spider '{spider_name}' completed successfully")
                return True
            else:
                print_error(f"Spider '{spider_name}' failed with code {e.code}")
                return False
        except Exception as e:
            os.chdir(original_cwd)
            sys.argv = original_argv
            print_error(f"Error running spider: {str(e)}")
            return False
            
    except ImportError:
        print_error("Could not import Scrapy - please ensure it's installed")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def populate_excel():
    print_info("Starting Excel population...")
    
    try:
        # Import the function from arranger_xlsx.py
        import sys
        sys.path.insert(0, os.getcwd())
        from arranger_xlsx import populate_sheet1_data
        
        populate_sheet1_data()
        print_success("Excel file populated successfully!")
        return True
    except Exception as e:
        print_error(f"Error populating Excel: {str(e)}")
        return False


def main():
    # First: Check if we need to re-run with correct Python
    script_dir = Path(__file__).parent
    venv_python = script_dir / ".venv" / "Scripts" / "python.exe"
    
    if venv_python.exists() and sys.executable.lower() != str(venv_python).lower():
        # Re-run with the correct Python from .venv
        print(f"Switching to .venv Python: {venv_python}")
        result = subprocess.run([str(venv_python), str(Path(__file__).absolute())])
        sys.exit(result.returncode)
    
    print_header("Steelite Product Scraper - Automated Runner")
    
    print_info(f"System: {sys.platform}")
    print_info(f"Python: {sys.version.split()[0]}")
    print_info(f"Python Executable: {sys.executable}")
    print_info(f"Working directory: {os.getcwd()}")
    
    # Check if we're in the right directory
    if not os.path.exists("steelite/steelite/spiders"):
        print_error("Error: Cannot find 'steelite/steelite/spiders' directory")
        print_error("Please run this script from the Web-Scraping-Test directory")
        sys.exit(1)
    
    # Statistics
    successful = 0
    failed = 0
    skipped = 0
    
    print_header("Running Spiders")
    
    for i, spider in enumerate(SPIDERS, 1):
        print(f"\n[{i}/{len(SPIDERS)}] {spider.upper()}")
        print("-" * 60)
        
        if run_spider(spider):
            successful += 1
            time.sleep(2)  # Small delay between spiders
        else:
            failed += 1
    
    # Summary of spider runs
    print_header("Spider Execution Summary")
    print(f"Total Spiders: {len(SPIDERS)}")
    print_success(f"Successful: {successful}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    if skipped > 0:
        print_warning(f"Skipped: {skipped}")
    
    if failed > 0:
        print_warning("\nSome spiders failed. Check the logs above for details.")
    
    # Populate Excel
    print_header("Populating Excel File")
    
    if populate_excel():
        print_success("All tasks completed!")
        print_info("Output file: results/STEELITE_Populated_v[X].xlsx")
    else:
        print_error("Excel population failed. Check the output above.")
        print_info("You can manually run 'python arranger_xlsx.py' to retry")
    
    print_header("Finished")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print_warning("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)
