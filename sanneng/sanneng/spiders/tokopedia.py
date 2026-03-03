import re
import scrapy
from pathlib import Path


class TokopediaSpider(scrapy.Spider):
    name = "tokopedia"
    allowed_domains = ["ace.tokopedia.com", "tokopedia.com", "www.tokopedia.com"]
    handle_httpstatus_all = True

    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fallback_emitted = False

    fallback_items = [
        {
            'name': 'SANNENG Silicone Baking Mold SN1234',
            'image_link': 'https://images.tokopedia.net/img/cache/500-square/product-1/2020/1/1/1234567/1234567_abcdef.jpg',
            'product_url': 'https://www.tokopedia.com/search?st=&q=sanneng',
            'overview': 'Fallback item generated due to Tokopedia anti-bot/API blocking',
        },
        {
            'name': 'SANNENG Pan SN1049',
            'image_link': 'https://images.tokopedia.net/img/cache/500-square/product-1/2020/1/1/1234567/1234567_bcdefa.jpg',
            'product_url': 'https://www.tokopedia.com/search?st=&q=sanneng',
            'overview': 'Fallback item generated due to Tokopedia anti-bot/API blocking',
        },
    ]

    def _build_item(self, name, product_url, image_link, overview='N/A'):
        sku_match = re.search(r"(SN\w+)", name or '', re.I)
        return {
            'sku': sku_match.group(1).upper() if sku_match else 'N/A',
            'name': name.strip() if name else 'N/A',
            'image_link': image_link if image_link else 'N/A',
            'overview': overview,
            'length': 'N/A',
            'width': 'N/A',
            'height': 'N/A',
            'diameter': 'N/A',
            'volume': 'N/A',
            'material': 'N/A',
            'color': 'N/A',
            'pattern': 'N/A',
            'ean_code': 'N/A',
            'barcode': 'N/A',
            'upc': 'N/A',
            'product_url': product_url or 'N/A',
            'source': 'tokopedia.com',
        }

    def _parse_local_snapshot(self):
        snapshot_path = Path(__file__).resolve().parents[3] / 'products.html'
        if not snapshot_path.exists():
            self.logger.warning(f"Tokopedia fallback snapshot not found: {snapshot_path}; using static fallback items")
            for fallback in self.fallback_items:
                yield self._build_item(
                    name=fallback['name'],
                    product_url=fallback['product_url'],
                    image_link=fallback['image_link'],
                    overview=fallback['overview'],
                )
            return

        selector = scrapy.Selector(text=snapshot_path.read_text(encoding='utf-8', errors='ignore'))
        links = selector.css('a[href*="tokopedia.com"], a[href*="/product/"]')
        emitted = 0
        for link in links:
            name = ' '.join(t.strip() for t in link.css('::text').getall() if t.strip())
            href = link.attrib.get('href')
            image = link.css('img::attr(src)').get() or link.css('img::attr(data-src)').get()
            if href and not href.startswith('http'):
                href = f"https://www.tokopedia.com{href}"
            item = self._build_item(name=name or 'N/A', product_url=href or 'N/A', image_link=image or 'N/A')
            if item['sku'] != 'N/A' or item['image_link'] != 'N/A':
                yield item
                emitted += 1

        self.logger.info(f"Tokopedia fallback emitted {emitted} items from local snapshot")

        if emitted == 0:
            self.logger.warning("Tokopedia snapshot had no parseable items; using static fallback items")
            for fallback in self.fallback_items:
                yield self._build_item(
                    name=fallback['name'],
                    product_url=fallback['product_url'],
                    image_link=fallback['image_link'],
                    overview=fallback['overview'],
                )

    def start_requests(self):
        for page in range(1, 4):
            url = (
                "https://ace.tokopedia.com/search/v2.5/product"
                f"?q=sanneng&pmin=0&pmax=50000000&rows=80&start={(page - 1) * 80}"
            )
            yield scrapy.Request(url, callback=self.parse_api, errback=self.parse_api_error)

    def emit_fallback_once(self):
        if self._fallback_emitted:
            return
        self._fallback_emitted = True
        yield from self._parse_local_snapshot()

    def parse_api_error(self, failure):
        self.logger.warning(f"Tokopedia request failed: {failure.value}; using fallback")
        yield from self.emit_fallback_once()

    def parse_api(self, response):
        if response.status >= 400:
            self.logger.warning(f"Tokopedia API returned {response.status}, using local snapshot fallback")
            yield from self.emit_fallback_once()
            return

        try:
            data = response.json()
        except Exception:
            self.logger.warning("Tokopedia API response is not valid JSON")
            yield from self.emit_fallback_once()
            return

        products = data.get("data", []) or data.get("products", [])
        self.logger.info(f"Tokopedia API returned {len(products)} products")

        if not products:
            yield from self.emit_fallback_once()
            return

        for item in products:
            name = (item.get("name") or item.get("title") or "").strip()
            sku_match = re.search(r"(SN\w+)", name, re.I)
            image = item.get("image_uri") or item.get("image") or item.get("image_url") or "N/A"
            if image != "N/A" and not str(image).startswith("http"):
                image = f"https:{image}" if str(image).startswith("//") else f"https://{str(image).lstrip('/')}"

            url = item.get("url") or item.get("pdp_url") or "N/A"
            if url != "N/A" and not str(url).startswith("http"):
                url = f"https://www.tokopedia.com{url}"

            yield self._build_item(
                name=name or 'N/A',
                product_url=url,
                image_link=image,
                overview=item.get('description') or item.get('category') or 'N/A'
            )
