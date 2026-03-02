import scrapy
import csv
import re
import json
from scrapy import Request


class WilliamsfoodequipmentSpider(scrapy.Spider):
    name = "williamsfoodequipment"
    allowed_domains = ["williamsfoodequipment.com"]
    start_urls = ["https://williamsfoodequipment.com/search.php?search_query=Steelite+"]
    csv_filename = "williamsfoodequipment_products.csv"
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'DOWNLOAD_DELAY': 2,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_data = []

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url,
                callback=self.parse,
                meta={'playwright': True}
            )

    def parse(self, response):
        product_links = response.css('li.klevuProduct a.klevuProductClick::attr(href)').getall()
        self.logger.info(f"Found {len(product_links)} product links")
        
        for link in set(product_links):
            if link:
                yield Request(
                    url=response.urljoin(link),
                    callback=self.parse_product,
                    dont_filter=False,
                    meta={'playwright': True}
                )
        
        # Handle pagination if needed
        next_page = response.css('a.pagination-next::attr(href)').get()
        if next_page:
            yield Request(
                url=response.urljoin(next_page),
                callback=self.parse,
                meta={'playwright': True}
            )

    def parse_product(self, response):
        product_name = (
            response.css('h1.productView-title::text').get() or
            response.xpath('//meta[@property="og:title"]/@content').get() or
            response.css('h1::text').get() or
            "N/A"
        )
        if isinstance(product_name, str):
            product_name = product_name.strip()

        image_url = (
            response.css('img.productView-image--default::attr(src)').get() or
            response.xpath('//meta[@property="og:image"]/@content').get() or
            response.css('img[class*="product"]::attr(src)').get() or
            "N/A"
        )
        if image_url and not image_url.startswith('http'):
            image_url = response.urljoin(image_url)

        overview_parts = response.css('div.productView-description ::text').getall()
        if not overview_parts:
            overview_parts = response.css('div[class*="description"] ::text').getall()
        overview = ' '.join([text.strip() for text in overview_parts if text.strip()])
        if len(overview) > 500:
            overview = overview[:500] + "..."

        specs = {}
        spec_rows = response.css('table.table.table-striped.table-bordered tbody tr')
        
        for row in spec_rows:
            spec_title = row.css('td.productView-specifications_title::text').get()
            spec_value = row.css('td.productView-specifications_value::text').get()
            
            if spec_title and spec_value:
                specs[spec_title.strip()] = spec_value.strip()
        
        # Extract specifications
        color = specs.get('Color', 'N/A')
        material = specs.get('Material', 'N/A')
        capacity = specs.get('Capacity', 'N/A')
        length = specs.get('Length', 'N/A')
        width = specs.get('Width', 'N/A')
        height = specs.get('Height', 'N/A')
        volume = specs.get('Volume', specs.get('Capacity', 'N/A'))
        diameter = specs.get('Diameter', 'N/A')
        pattern = specs.get('Pattern', 'N/A')
        
        # Extract codes
        sku = response.xpath('//span[contains(text(), "SKU:")]/following-sibling::span/text()').get()
        if not sku:
            sku = response.css('span.product_sku::text').get() or "N/A"

        mfr = specs.get('MFR') or specs.get('Manufacturer Code') or specs.get('Mfr') or sku or "N/A"
        
        # Try to extract from BCData JavaScript
        if mfr == "N/A":
            bcdata_script = response.xpath('//script[contains(text(), "var BCData")]/text()').get()
            if bcdata_script:
                try:
                    match = re.search(r'var BCData = ({.*?});', bcdata_script, re.DOTALL)
                    if match:
                        bcdata = json.loads(match.group(1))
                        mfr = bcdata.get('product_attributes', {}).get('mpn', 'N/A')
                except (json.JSONDecodeError, AttributeError):
                    pass

        ean_code = specs.get('EAN Code') or specs.get('EAN') or specs.get('EAN13') or 'N/A'
        barcode = specs.get('Barcode') or specs.get('UPC') or specs.get('Barcode/EAN') or 'N/A'

        product = {
            'name': product_name,
            'item_sku': sku,
            'model_number': specs.get('Model', 'N/A'),
            'manufacturer': mfr,
            'image_link': image_url,
            'overview': overview or 'N/A',
            'material': material,
            'color': color,
            'pattern': pattern,
            'length': length,
            'width': width,
            'height': height,
            'volume_capacity': volume,
            'diameter': diameter,
            'country_of_origin': specs.get('Country of Origin', 'N/A'),
            'upc_barcode': barcode,
            'ean_code': ean_code,
            'hazmat': specs.get('Hazmat', 'N/A'),
            'oversize': specs.get('Oversize', 'N/A'),
            'marketplace_uom': specs.get('UOM', 'N/A'),
            'product_url': response.url,
        }

        self.product_data.append(product)
        self.logger.info(f"✓ Scraped: {product_name}")
        yield product

    def closed(self, reason):
        self.save_to_csv(self.csv_filename)
        self.logger.info(f"Total products scraped: {len(self.product_data)}")

    def save_to_csv(self, filename):
        if not self.product_data:
            self.logger.info("No product data to save")
            return
        
        fieldnames = [
            'name', 'item_sku', 'model_number', 'manufacturer',
            'image_link', 'overview', 'material', 'color', 'pattern',
            'length', 'width', 'height', 'volume_capacity', 'diameter',
            'country_of_origin', 'upc_barcode', 'ean_code',
            'hazmat', 'oversize', 'marketplace_uom', 'product_url'
        ]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.product_data)
            self.logger.info(f"✓ Saved {len(self.product_data)} products to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
