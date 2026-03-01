import re
import scrapy
from scrapy_playwright.page import PageMethod


class SteelitePlaywrightSpider(scrapy.Spider):
    name = "steelite_playwright"
    allowed_domains = ["steelite-utopia.com"]
    start_urls = ["https://www.steelite-utopia.com/products"]

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
        self.logger.info(f"Found cards: {len(cards)}")

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

        product_code = info_values[0] if len(info_values) > 0 else response.meta.get("listing_code")
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
        material = kv.get("material")
        color = kv.get("colour") or kv.get("color")
        barcode = kv.get("outer barcode") or kv.get("barcode")
        ean_code = kv.get("ean code") or kv.get("ean")
        pattern = kv.get("pattern")

        # optional dimensions (if present in keys)
        length = kv.get("length")
        width = kv.get("width")
        height = kv.get("height")
        diameter = kv.get("diameter")
        volume = kv.get("volume")

        # fallback parse from title if missing
        if not (length and width and height):
            dim3 = self._extract_measure(title, r"(\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?\s*cm)")
            if dim3:
                parts = re.findall(r"\d+(?:\.\d+)?", dim3)
                if len(parts) >= 3:
                    length = length or f"{parts[0]} cm"
                    width = width or f"{parts[1]} cm"
                    height = height or f"{parts[2]} cm"

        if not diameter:
            d = self._extract_measure(title, r"(\d+(?:\.\d+)?)\s*cm")
            if d:
                diameter = f"{d} cm"

        if not volume:
            v = self._extract_measure(title, r"(\d+(?:\.\d+)?\s*(?:cl|ml|l|ltr|oz))")
            if v:
                volume = v

        yield {
            "product_url": response.url,
            "product_name": title or response.meta.get("listing_name"),
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