import scrapy
import csv
import re
from scrapy_playwright.page import PageMethod


class UsSteeliteSpider(scrapy.Spider):
    name = "us_steelite"
    allowed_domains = ["us.steelite.com"]
    start_urls = ["https://us.steelite.com/"]
    csv_filename = "us_steelite_products.csv"
    
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 2,
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler": 585,
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_data = []

    def parse(self, response):
        # Search for Steelite products
        yield scrapy.Request(
            "https://us.steelite.com/search?q=steelite",
            callback=self.parse_search_results,
            meta={"playwright": True}
        )

    def parse_search_results(self, response):
        # Find all product links
        product_links = response.css('a.product-item-photo::attr(href)').getall()
        self.logger.info(f"Found {len(product_links)} product links")
        
        for product_url in product_links:
            if product_url:
                yield scrapy.Request(
                    url=response.urljoin(product_url),
                    callback=self.parse_product,
                    meta={"playwright": True}
                )
        
        # Check for pagination
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page),
                callback=self.parse_search_results,
                meta={"playwright": True}
            )

    def parse_product(self, response):
        # Main product details
        product_name = (
            response.css('h1.page-title span::text').get() or
            response.css('h1::text').get() or
            "N/A"
        ).strip() if response.css('h1.page-title span::text').get() or response.css('h1::text').get() else "N/A"

        # Product code - usually in SKU format
        product_code = (
            response.css('span.sku::text').get() or
            response.xpath("//meta[@itemprop='sku']/@content").get() or
            "N/A"
        )
        if isinstance(product_code, str):
            product_code = product_code.strip()

        # Image
        image_link = (
            response.css('img.gallery-photo__image::attr(src)').get() or
            response.xpath('//meta[@property="og:image"]/@content').get() or
            response.css('img.product-image::attr(src)').get() or
            "N/A"
        )
        if image_link and not image_link.startswith('http'):
            image_link = response.urljoin(image_link)

        # Description/Overview
        overview_parts = response.css('div.product-description ::text').getall()
        overview = ' '.join([t.strip() for t in overview_parts if t.strip()]) if overview_parts else "N/A"
        if len(overview) > 500:
            overview = overview[:500] + "..."

        # Specifications from table or list
        specs = {}
        
        # Try table format first
        spec_rows = response.css('table.attributes tr, table.specs tr')
        for row in spec_rows:
            cells = row.css('td::text').getall()
            if len(cells) >= 2:
                key = cells[0].strip().lower()
                value = cells[1].strip()
                specs[key] = value
        
        # Try definition list format
        dts = response.css('dt::text').getall()
        dds = response.css('dd::text').getall()
        for dt, dd in zip(dts, dds):
            key = dt.strip().lower()
            value = dd.strip()
            specs[key] = value

        # Extract dimensions and properties
        material = specs.get('material', specs.get('material type', 'N/A'))
        color = specs.get('color', specs.get('colour', 'N/A'))
        pattern = specs.get('pattern', specs.get('design', 'N/A'))
        
        # Try to extract dimensions from product name or specs
        diameter = specs.get('diameter', 'N/A')
        length = specs.get('length', 'N/A')
        width = specs.get('width', 'N/A')
        height = specs.get('height', specs.get('depth', 'N/A'))
        volume_capacity = specs.get('capacity', specs.get('volume', 'N/A'))

        # Try to extract from product name if not found in specs
        if diameter == 'N/A' and product_name:
            dim_match = re.search(r'(\d+(?:\.\d+)?)\s*cm', product_name, re.I)
            if dim_match:
                diameter = f"{dim_match.group(1)} cm"

        if volume_capacity == 'N/A' and product_name:
            vol_match = re.search(r'(\d+(?:\.\d+)?(?:\s*\d+/\d+)?)\s*(cl|ml|oz|fl\s*oz)', product_name, re.I)
            if vol_match:
                volume_capacity = f"{vol_match.group(1)} {vol_match.group(2)}"

        # Barcode/EAN
        upc_barcode = specs.get('upc', specs.get('barcode', specs.get('ean', 'N/A')))
        ean_code = specs.get('ean', specs.get('ean code', 'N/A'))

        # Country
        country_of_origin = specs.get('country of origin', specs.get('made in', 'N/A'))

        product = {
            "name": product_name,
            "item_sku": product_code,
            "model_number": specs.get('model', 'N/A'),
            "manufacturer": product_code,  # Using product code as manufacturer identifier
            "image_link": image_link,
            "overview": overview,
            "material": material,
            "color": color,
            "pattern": pattern,
            "length": length,
            "width": width,
            "height": height,
            "volume_capacity": volume_capacity,
            "diameter": diameter,
            "country_of_origin": country_of_origin,
            "upc_barcode": upc_barcode,
            "ean_code": ean_code,
            "hazmat": specs.get('hazmat', 'N/A'),
            "oversize": specs.get('oversize', 'N/A'),
            "marketplace_uom": specs.get('uom', 'N/A'),
            "product_url": response.url,
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
