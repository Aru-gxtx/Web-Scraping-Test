@echo off
REM Steelite Product Scraper - Batch Runner for Windows
REM This script runs all spiders and populates the STEELITE.xlsx file

SETLOCAL ENABLEDELAYEDEXPANSION
title Steelite Product Scraper

REM Set Python executable - use the one from the current environment
for /f "tokens=*" %%I in ('where python') do set PYTHON_EXE=%%I

if "!PYTHON_EXE!"=="" (
    echo Error: Python not found in PATH
    echo Please ensure Python is installed and in your PATH
    pause
    exit /b 1
)

echo.
echo ============================================================
echo          Steelite Product Scraper - Batch Runner
echo ============================================================
echo.
echo Using Python: !PYTHON_EXE!
echo.

REM Check if we're in the right directory
if not exist "steelite\steelite\spiders" (
    echo Error: Cannot find 'steelite\steelite\spiders' directory
    echo Please run this script from the Web-Scraping-Test directory
    pause
    exit /b 1
)

REM Initialize counters
set successful=0
set failed=0

echo [INFO] Starting spider execution...
echo.

REM Run each spider
for %%S in (steelitehome steelite_playwright webstaurantstore_vendor stephensons kitchenrestock us_steelite williamsfoodequipment) do (
    echo.
    echo ============================================================
    echo Running Spider: %%S
    echo ============================================================
    
    cd steelite
    !PYTHON_EXE! -m scrapy crawl %%S
    
    if errorlevel 1 (
        echo [ERROR] Spider '%%S' failed!
        set /a failed+=1
    ) else (
        echo [SUCCESS] Spider '%%S' completed!
        set /a successful+=1
    )
    
    cd ..
    timeout /t 2 /nobreak > nul
)

REM Print summary
echo.
echo ============================================================
echo                 Execution Summary
echo ============================================================
echo Successful: !successful!
echo Failed: !failed!
echo.

if !failed! gtr 0 (
    echo [WARNING] Some spiders failed. Check the output above.
) else (
    echo [SUCCESS] All spiders completed successfully!
)

echo.
echo ============================================================
echo        Populating STEELITE.xlsx with scraped data
echo ============================================================
echo.

!PYTHON_EXE! arranger_xlsx.py

if errorlevel 1 (
    echo [ERROR] Excel population failed!
    echo You can manually run '!PYTHON_EXE! arranger_xlsx.py' to retry
) else (
    echo [SUCCESS] Excel file populated successfully!
    echo Output file: results/STEELITE_Populated_v[X].xlsx
)

echo.
echo ============================================================
echo                    Process Complete
echo ============================================================
echo.

pause
