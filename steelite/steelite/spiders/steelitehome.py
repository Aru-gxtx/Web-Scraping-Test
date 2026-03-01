import re
import scrapy
from scrapy_playwright.page import PageMethod


class SteelitehomeSpider(scrapy.Spider):
    name = "steelitehome"
    allowed_domains = ["www.steelitehome.com"]
    start_urls = ["https://www.steelitehome.com"]

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,
    }

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
        
        self.logger.info(f"Found {len(range_links)} ranges in {response.url}")
        
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
        
        self.logger.info(f"Found {len(product_cards)} products in {response.url}")
        
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
            # Extract Product Code - clean whitespace and newlines
            code_match = re.search(r'Product Code:\s*(\S+)', attributes_text, re.I)
            if code_match:
                product_code = code_match.group(1).strip().replace('\n', '').replace('<br', '')
            
            # Extract Item name
            item_match = re.search(r'Item:\s*(.+?)(?=<br|$)', attributes_text, re.I)
            if item_match:
                item_name = item_match.group(1).strip()
            
            # Extract Colour
            colour_match = re.search(r'Colour:\s*(.+?)(?=<br|$)', attributes_text, re.I)
            if colour_match:
                color = colour_match.group(1).strip()

        # Product name from h1
        product_name = response.css("#productTop h1::text").get()
        if product_name:
            product_name = product_name.strip()

        # Image link - first image in gallery
        image_link = response.css(".owl-carousel.gallery a.thumbnail::attr(href)").get()
        if image_link:
            image_link = response.urljoin(image_link)

        # Material, Pattern, Range from specification table
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

        # Overview/Description from long description section
        overview = response.css("#longDescription .wysiwyg p::text").getall()
        overview = " ".join([p.strip() for p in overview if p.strip()]) if overview else None

        # Dimensions from product name (if present)
        length = None
        width = None
        height = None
        diameter = None
        volume = None

        # Try to extract dimensions from product name
        if product_name:
            # Look for patterns like "13cm (5")" or "28cm x 22cm"
            dim_match = re.search(r'(\d+(?:\.\d+)?)\s*cm', product_name, re.I)
            if dim_match:
                diameter = f"{dim_match.group(1)} cm"
            
            # Look for volume patterns like "43.5cl" or "(15 1/3oz)"
            vol_match = re.search(r'(\d+(?:\.\d+)?(?:\s*\d+/\d+)?)\s*(cl|ml|oz)', product_name, re.I)
            if vol_match:
                volume = f"{vol_match.group(1)} {vol_match.group(2)}"

        yield {
            "product_url": response.url,
            "product_name": product_name or item_name,
            "product_code": product_code,
            "image_link": image_link,
            "overview": overview,
            "length": length,
            "width": width,
            "height": height,
            "volume": volume,
            "diameter": diameter,
            "color": color,
            "material": material,
            "ean_code": ean_code,
            "pattern": pattern,
            "barcode": barcode,
        }
