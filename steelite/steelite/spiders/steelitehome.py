import re
import scrapy
import csv
from scrapy_playwright.page import PageMethod


class SteelitehomeSpider(scrapy.Spider):
    name = "steelitehome"
    allowed_domains = ["www.steelitehome.com"]
    start_urls = ["https://www.steelitehome.com"]
    csv_filename = "steelitehome_products.csv"

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_data = []

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "a.slide", timeout=90000),
                        PageMethod("wait_for_timeout", 1500),
                    ],
                },
                callback=self.parse_categories,
            )

    def parse_categories(self, response):
        category_links = response.css("a.slide::attr(href)").getall()
        self.logger.info(f"Found {len(category_links)} main categories")
        
        for link in category_links:
            category_url = response.urljoin(link)
            yield scrapy.Request(
                category_url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", ".rangeBox", timeout=90000),
                        PageMethod("wait_for_timeout", 1500),
                    ],
                },
                callback=self.parse_subcategories,
            )

    def parse_subcategories(self, response):
        range_links = response.css("a.rangeBox::attr(href)").getall()
        self.logger.info(f"Found {len(range_links)} ranges")
        
        for link in range_links:
            range_url = response.urljoin(link)
            yield scrapy.Request(
                range_url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", ".productBox", timeout=90000),
                        PageMethod("wait_for_timeout", 1500),
                    ],
                },
                callback=self.parse_product_list,
            )

    def parse_product_list(self, response):
        product_cards = response.css("div.productBox")
        self.logger.info(f"Found {len(product_cards)} products")
        
        for card in product_cards:
            product_url = card.css("a::attr(href)").get()
            if product_url:
                product_url = response.urljoin(product_url)
                yield scrapy.Request(
                    product_url,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_selector", "#product", timeout=90000),
                            PageMethod("wait_for_timeout", 1500),
                        ],
                    },
                    callback=self.parse_product,
                )

    def parse_product(self, response):
        product_code = None
        item_name = None
        color = None
        
        attributes_text = response.css("#attributes::text").getall()
        attributes_text = " ".join(attributes_text)
        
        if attributes_text:
            code_match = re.search(r'Product Code:\s*(\S+)', attributes_text, re.I)
            if code_match:
                product_code = code_match.group(1).strip().replace('\n', '').replace('<br', '')
            
            item_match = re.search(r'Item:\s*(.+?)(?=<br|$)', attributes_text, re.I)
            if item_match:
                item_name = item_match.group(1).strip()
            
            colour_match = re.search(r'Colour:\s*(.+?)(?=<br|$)', attributes_text, re.I)
            if colour_match:
                color = colour_match.group(1).strip()

        product_name = response.css("#productTop h1::text").get()
        if product_name:
            product_name = product_name.strip()

        image_link = response.css(".owl-carousel.gallery a.thumbnail::attr(href)").get()
        if image_link:
            image_link = response.urljoin(image_link)

        material = None
        pattern = None
        ean_code = None
        barcode = None
        
        spec_rows = response.css("table.table-bordered tbody tr")
        for row in spec_rows:
            label = row.css("td:nth-child(1)::text").get()
            value = row.css("td:nth-child(2)::text").get()
            
            if label and value:
                label_lower = label.strip().lower()
                value_clean = value.strip()
                
                if 'material' in label_lower:
                    material = value_clean
                elif 'pattern code' in label_lower:
                    pattern = value_clean
                elif 'ean' in label_lower:
                    ean_code = value_clean
                elif 'barcode' in label_lower:
                    barcode = value_clean

        overview = response.css("#longDescription .wysiwyg p::text").getall()
        overview = " ".join([p.strip() for p in overview if p.strip()]) if overview else None

        product = {
            "name": product_name or item_name or "N/A",
            "item_sku": product_code or "N/A",
            "model_number": "N/A",
            "manufacturer": product_code or "N/A",
            "image_link": image_link or "N/A",
            "overview": overview or "N/A",
            "material": material or "N/A",
            "color": color or "N/A",
            "pattern": pattern or "N/A",
            "length": "N/A",
            "width": "N/A",
            "height": "N/A",
            "volume_capacity": "N/A",
            "diameter": "N/A",
            "country_of_origin": "N/A",
            "upc_barcode": barcode or "N/A",
            "ean_code": ean_code or "N/A",
            "hazmat": "N/A",
            "oversize": "N/A",
            "marketplace_uom": "N/A",
            "product_url": response.url,
        }
        
        self.product_data.append(product)
        self.logger.info(f"✓ Scraped: {product['name']}")
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
