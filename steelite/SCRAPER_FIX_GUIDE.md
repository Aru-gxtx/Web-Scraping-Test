# Williams Food Equipment Scraper - Fix Guide

## Problem
The website is returning **403 Forbidden** responses when Scrapy makes requests. This is a common anti-scraping measure.

## Root Causes
1. **Website blocks standard HTTP requests** - williamsfoodequipment.com actively detects and blocks Scrapy/bot requests
2. **JavaScript-based content loading** - The product data is loaded dynamically via JavaScript
3. **Missing referrer/cookies** - Website may require proper browser-like session context

## Solutions Implemented

### 1. ✅ Custom Middleware (DONE)
- Added `CustomHttpErrorMiddleware` to handle 403 responses
- Configured `HTTPERROR_ALLOWED_CODES = [403]` in settings
- **Result**: Middleware works but 403 pages contain no product data

### 2. ✅ Browser Headers (DONE)
- Added real Chrome User-Agent
- Configured `DEFAULT_REQUEST_HEADERS` with browser-like headers  
- Disabled `ROBOTSTXT_OBEY = False`
- **Result**: Requests still blocked

### 3. ✅ Playwright Integration (IN PROGRESS)
- Enabled Scrapy-Playwright for JavaScript rendering
- Spider now requests with `meta={'playwright': True}`
- Uses Chromium browser to render pages
- **Status**: Should bypass 403 since rendering through real browser

## Running the Scraper

### Option 1: Playwright Rendering (Recommended)
```powershell
cd c:\Users\admin\Documents\GitHub\Web-Scraping-Test\steelite
py -m scrapy crawl williamsfoodequipment -O output.csv
```

**Note**: First run may take 2-3 minutes as Playwright downloads and starts Chromium browser. Subsequent runs are faster.

### Option 2: With Detailed Logging
```powershell
py -m scrapy crawl williamsfoodequipment -O output.csv -L DEBUG
```

## Expected Output
The CSV will contain columns:
- product_name
- url
- image_link
- brand, series, type
- capacity, color, material, size
- length, width, height, volume, diameter
- case_pack_size, pattern
- sku, ean_code, barcode
- warranty
- sale_price, regular_price
- in_stock
- overview
- all_specs (raw specifications dict)

## If It Still Doesn't Work

### Fallback Option 1: Manual Direct Request
```powershell
# Save the search page HTML first
curl -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" `
  -H "Referer: https://williamsfoodequipment.com/" `
  "https://williamsfoodequipment.com/search.php?search_query=Steelite+" `
  -o search_page.html
```

### Fallback Option 2: Use Selenium
If Playwright fails, you can use Selenium with Chrome driver:
```python
from selenium import webdriver

driver = webdriver.Chrome()
driver.get("https://williamsfoodequipment.com/search.php?search_query=Steelite+")
html = driver.page_source
```

### Fallback Option 3: API Approach
Check if the website has a hidden API endpoint by:
1. Opening browser DevTools (F12)
2. Going to Network tab
3. Searching for XHR requests during page load
4. Use those API URLs directly if found

## Files Modified

1. **steelite/spiders/williamsfoodequipment.py**
   - Added Playwright configuration
   - Added better logging
   - Improved CSS selector fallbacks
   - Start requests now use `meta={'playwright': True}`

2. **steelite/settings.py**
   - Changed `ROBOTSTXT_OBEY = False`
   - Added real User-Agent
   - Added `DEFAULT_REQUEST_HEADERS`
   - Added `HTTPERROR_ALLOWED_CODES = [403]`
   - Enabled `CustomHttpErrorMiddleware`

3. **steelite/middlewares.py**
   - Added `CustomHttpErrorMiddleware` class to handle 403s

## Troubleshooting

### Issue: "NotImplementedError: method not found" 
- Solution: Run `pip install scrapy-playwright`

### Issue: Playwright browser won't download
- Solution: Run `python -m playwright install chromium`

### Issue: Still getting no results
- Solutions:
  1. Check if selectors match actual HTML (open page source in browser)
  2. Try with proxy rotation (pip install scrapy-rotating-proxy)
  3. Try with request delay increase: `DOWNLOAD_DELAY = 3` or higher

## Next Steps

1. Run with Playwright enabled
2. Check the generated CSV file in `steelite/` directory
3. If successful, data will be exported
4. If still failing, inspect actual HTML response to verify selectors

---
**Last Updated**: 2026-03-01
**Status**: Playwright implementation in progress
