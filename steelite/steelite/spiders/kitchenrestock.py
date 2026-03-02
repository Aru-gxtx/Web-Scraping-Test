import re
import scrapy
import csv
from scrapy_playwright.page import PageMethod


class KitchenrestockSpider(scrapy.Spider):
    name = "kitchenrestock"
    allowed_domains = ["kitchenrestock.com"]
    csv_filename = "kitchenrestock_products.csv"

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 25,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 15,
        "AUTOTHROTTLE_MAX_DELAY": 180,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 0.1,
        "RETRY_TIMES": 8,
        "RETRY_HTTP_CODES": [429, 500, 502, 503, 504, 522, 524, 408],
        "HTTPERROR_ALLOWED_CODES": [429],
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler": 585,
        },
    }

    def __init__(self, start_page=1, end_page=861, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_page = int(start_page)
        self.end_page = int(end_page)
        self.seen = set()
        self.product_data = []

    def start_requests(self):
        yield scrapy.Request(
            self._search_url(self.start_page),
            callback=self.parse_search,
            cb_kwargs={"page": self.start_page},
            dont_filter=True,
            meta={"playwright": True},
        )

    def _search_url(self, page: int) -> str:
        return f"https://kitchenrestock.com/search?options%5Bprefix%5D=last&page={page}&q=Steelite+"

    def parse_search(self, response, page: int):
        if response.status == 429:
            retry_after = int(response.headers.get("Retry-After", b"60").decode("utf-8", "ignore") or 60)
            self.logger.warning("429 on page=%s, retry-after=%ss", page, retry_after)
            yield response.request.replace(dont_filter=True, priority=response.request.priority - 10)
            return

        links = response.css("li.js-pagination-result a.js-prod-link::attr(href)").getall()
        if not links:
            links = response.css("product-card a.js-prod-link::attr(href)").getall()

        self.logger.info(f"Found {len(links)} products on page {page}")

        for href in links:
            url = response.urljoin(href.split("?")[0])
            if url in self.seen:
                continue
            self.seen.add(url)
            yield scrapy.Request(url, callback=self.parse_product, meta={"playwright": True})

        if page < self.end_page and links:
            next_page = page + 1
            yield scrapy.Request(
                self._search_url(next_page),
                callback=self.parse_search,
                cb_kwargs={"page": next_page},
                dont_filter=True,
                meta={"playwright": True},
            )

    def parse_product(self, response):
        product_name = (
            response.css('h1.heading-title::text').get() or
            response.css('h1::text').get() or
            response.xpath('//meta[@property="og:title"]/@content').get() or
            "N/A"
        )
        if isinstance(product_name, str):
            product_name = product_name.strip()

        # SKU/Model
        item_sku = (
            response.xpath("//span[contains(text(), 'SKU')]/following-sibling::span/text()").get() or
            response.css('span.product-sku::text').get() or
            response.xpath("//meta[@itemprop='sku']/@content").get() or
            "N/A"
        )
        if isinstance(item_sku, str):
            item_sku = item_sku.strip()

        # Image
        image_link = (
            response.css('img.product-image::attr(src)').get() or
            response.xpath('//meta[@property="og:image"]/@content').get() or
            "N/A"
        )
        if image_link and not image_link.startswith('http'):
            image_link = response.urljoin(image_link)

        # Description
        overview_parts = response.css('div.product-description::text, div.product-details::text').getall()
        overview = ' '.join([t.strip() for t in overview_parts if t.strip()]) if overview_parts else "N/A"
        if len(overview) > 500:
            overview = overview[:500] + "..."

        # Specifications
        specs = {}
        spec_rows = response.css('table.specs tr, div.specs-row')
        for row in spec_rows:
            cells = row.css('td::text, span.spec-label::text, span.spec-value::text').getall()
            if len(cells) >= 2:
                key = cells[0].strip().lower()
                value = cells[1].strip() if len(cells) > 1 else ""
                specs[key] = value

        # Extract fields
        material = specs.get('material', specs.get('material type', 'N/A'))
        color = specs.get('color', specs.get('colour', 'N/A'))
        pattern = specs.get('pattern', specs.get('pattern name', 'N/A'))
        length = specs.get('length', specs.get('width', 'N/A'))
        width = specs.get('width', specs.get('length', 'N/A'))
        height = specs.get('height', specs.get('depth', 'N/A'))
        diameter = specs.get('diameter', 'N/A')
        volume_capacity = specs.get('capacity', specs.get('volume', 'N/A'))
        upc_barcode = specs.get('upc', specs.get('barcode', 'N/A'))
        ean_code = specs.get('ean', specs.get('ean code', 'N/A'))

        product = {
            "name": product_name,
            "item_sku": item_sku,
            "model_number": specs.get('model', 'N/A'),
            "manufacturer": item_sku,
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
            "country_of_origin": specs.get('country of origin', 'N/A'),
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
