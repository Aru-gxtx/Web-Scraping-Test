import re
import scrapy
import csv
from scrapy_playwright.page import PageMethod


class SteelitePlaywrightSpider(scrapy.Spider):
    name = "steelite_playwright"
    allowed_domains = ["steelite-utopia.com"]
    start_urls = ["https://www.steelite-utopia.com/products"]
    csv_filename = "utopia_products.csv"

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
                        PageMethod("wait_for_selector", "a.product-entry-grid", timeout=90000),
                        PageMethod("wait_for_timeout", 1500),
                    ],
                },
                callback=self.parse,
            )

    def parse(self, response):
        cards = response.css("a.product-entry-grid")
        self.logger.info(f"Found {len(cards)} products")

        for c in cards:
            href = c.attrib.get("href")
            if not href:
                continue

            yield scrapy.Request(
                response.urljoin(href),
                meta={
                    "playwright": True,
                    "expected_code": c.attrib.get("data-product"),
                    "listing_name": (c.css(".product-entry-name::text").get() or "").strip(),
                    "listing_code": (c.css(".product-entry-code::text").get() or "").strip(),
                    "listing_image": c.css("img.product-entry-image-inner::attr(src)").get(),
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", ".popup[data-key='productCard'] .info-details .info-title", timeout=90000),
                        PageMethod("wait_for_timeout", 1200),
                    ],
                },
                callback=self.parse_product,
            )

    def _extract_measure(self, text, pattern):
        if not text:
            return None
        m = re.search(pattern, text, flags=re.I)
        return m.group(1).strip() if m else None

    def parse_product(self, response):
        title = (response.css(".popup[data-key='productCard'] .info-details .info-title::text").get() or "").strip()

        info_values = response.css(".popup[data-key='productCard'] .info-details > .info-value::text").getall()
        info_values = [v.strip() for v in info_values if v and v.strip()]

        product_code = info_values[0] if len(info_values) > 0 else response.meta.get("listing_code", "N/A")
        overview = info_values[1] if len(info_values) > 1 else None

        image_link = response.css(".popup[data-key='productCard'] img.info-image-inner::attr(src)").get()
        image_link = response.urljoin(image_link) if image_link else None

        kv = {}
        for row in response.css(".popup[data-key='productCard'] .info-col1 > div"):
            k = (row.css("span.info-key::text").get() or "").strip().lower()
            v = (row.css("span.info-value::text").get() or "").strip()
            if k:
                kv[k] = v

        # direct fields
        material = kv.get("material", "N/A")
        color = kv.get("colour") or kv.get("color") or "N/A"
        barcode = kv.get("outer barcode") or kv.get("barcode") or "N/A"
        ean_code = kv.get("ean code") or kv.get("ean") or "N/A"
        pattern = kv.get("pattern", "N/A")

        # optional dimensions
        length = kv.get("length", "N/A")
        width = kv.get("width", "N/A")
        height = kv.get("height", "N/A")
        diameter = kv.get("diameter", "N/A")
        volume_capacity = kv.get("volume", "N/A")

        # fallback parse from title if missing
        if length == "N/A" or width == "N/A" or height == "N/A":
            dim3 = self._extract_measure(title, r"(\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?\s*cm)")
            if dim3:
                parts = re.findall(r"\d+(?:\.\d+)?", dim3)
                if len(parts) >= 3:
                    length = length if length != "N/A" else f"{parts[0]} cm"
                    width = width if width != "N/A" else f"{parts[1]} cm"
                    height = height if height != "N/A" else f"{parts[2]} cm"

        if diameter == "N/A":
            d = self._extract_measure(title, r"(\d+(?:\.\d+)?)\s*cm")
            if d:
                diameter = f"{d} cm"

        if volume_capacity == "N/A":
            v = self._extract_measure(title, r"(\d+(?:\.\d+)?\s*(?:cl|ml|l|ltr|oz))")
            if v:
                volume_capacity = v

        product = {
            "name": title or response.meta.get("listing_name", "N/A"),
            "item_sku": product_code,
            "model_number": "N/A",
            "manufacturer": product_code,
            "image_link": image_link or "N/A",
            "overview": overview or "N/A",
            "material": material,
            "color": color,
            "pattern": pattern,
            "length": length,
            "width": width,
            "height": height,
            "volume_capacity": volume_capacity,
            "diameter": diameter,
            "country_of_origin": "N/A",
            "upc_barcode": barcode,
            "ean_code": ean_code,
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