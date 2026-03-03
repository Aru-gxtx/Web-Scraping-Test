# SANNENG Product Scraping Project

This project scrapes SANNENG product data from multiple websites and populates a master Excel file.

## Websites Scraped

1. **chakawal.com** - 26 pages of SANNENG products
2. **sannengvietnam.com** - 4 pages of products (Vietnamese)
3. **tokopedia.com** - Search results for "Sanneng" (Indonesian)
4. **unopan.tw** - Search results for "SANNENG" (Chinese/Taiwan)
5. **coupang.tw** - Up to 27 pages of SANNENG products (Chinese/Taiwan)

## Data Collected

For each product, the spiders attempt to collect:
- SKU/Model Number (MFR)
- Product Name
- Image Link
- Overview/Description
- Dimensions (Length, Width, Height)
- Volume/Capacity
- Diameter
- Color
- Material
- Pattern
- EAN Code
- Barcode/UPC

## Project Structure

```
sanneng/
├── scrapy.cfg                      # Scrapy configuration
├── sanneng/
│   ├── __init__.py
│   ├── items.py                    # Item definitions
│   ├── middlewares.py
│   ├── pipelines.py
│   ├── settings.py                 # Spider settings
│   └── spiders/
│       ├── __init__.py
│       ├── chakawal.py             # Chakawal spider
│       ├── sannengvietnam.py       # Sanneng Vietnam spider
│       ├── tokopedia.py            # Tokopedia spider
│       ├── unopan.py               # Unopan spider
│       └── coupang.py              # Coupang spider
└── sanneng_arranger_xlsx.py        # Excel populator script
```

## Installation

1. Make sure you have Python 3.8+ installed
2. Install required packages:
```bash
pip install scrapy pandas openpyxl
```

## Usage

### Step 1: Run the Spiders

Navigate to the sanneng directory and run each spider:

```bash
cd sanneng

# Run individual spiders
scrapy crawl chakawal -O chakawal_products.csv
scrapy crawl sannengvietnam -O sannengvietnam_products.csv
scrapy crawl tokopedia -O tokopedia_products.csv
scrapy crawl unopan -O unopan_products.csv
scrapy crawl coupang -O coupang_products.csv
```

Or run all spiders at once from the root directory:

```bash
python run_sanneng_spiders.py
```

### Step 2: Populate the Excel File

After scraping, run the arranger script to populate the SAN NENG.xlsx file:

```bash
python sanneng_arranger_xlsx.py
```

This will:
- Load all scraped CSV files
- Match products by SKU/MFR
- Populate columns E onwards in the Excel file
- Save the result as `SAN NENG_updated.xlsx`

## Important Notes

### SKU Extraction
- The primary matching key is SKU/Model Number (usually in format SN####)
- SKUs are normalized (uppercase, trimmed) for matching
- The script will only populate empty cells, preserving existing data

### Excel File
- The original `SAN NENG.xlsx` file should be in the `sources/` directory
- The script starts populating from column E onwards (columns A-D are preserved)
- A new file `SAN NENG_updated.xlsx` is created with the populated data

### Website Limitations
- **Tokopedia** and **Coupang**: These sites use heavy JavaScript rendering. The spiders may need Selenium or Playwright for better results.
- **Rate Limiting**: Spiders have built-in delays to respect website servers. Adjust `DOWNLOAD_DELAY` in settings if needed.
- **Language**: Some sites are in Vietnamese, Chinese, or Indonesian. The scrapers handle these languages.

###Performance Tips
1. Test individual spiders first before running all
2. Check the CSV output to verify data quality
3. Adjust selectors in spider files if websites change their structure
4. Use `-O` flag with scrapy to overwrite previous CSV files

## Troubleshooting

### No products scraped
- Check if the website structure has changed
- Verify the CSS selectors in the spider file
- Look at the spider's log output for errors

### JavaScript-heavy sites not working
Consider using:
- Scrapy-Splash or Scrapy-Selenium for JavaScript rendering
- Playwright for modern async scraping
- API endpoints if available

### Encoding issues
- All CSV files are saved with UTF-8 encoding
- Excel files use openpyxl engine which handles international characters

## Future Improvements

1. Add Selenium/Playwright integration for JavaScript-heavy sites
2. Implement retry logic for failed requests
3. Add data validation and cleaning
4. Create a web interface for monitoring scraping progress
5. Implement incremental updates instead of full rescrapes

## License

This project is for educational purposes. Please respect each website's robots.txt and terms of service.
