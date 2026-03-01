import scrapy
import json
from scrapy_playwright.page import PageMethod

class SteeliteSpider(scrapy.Spider):
    name = "steelite"
    allowed_domains = ["www.steelite.com"]
    start_urls = ["https://www.steelite.com/tableware.html"]

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 2,
        'HTTPERROR_ALLOWED_CODES': [403, 503], 
        
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        
        'PLAYWRIGHT_BROWSER_TYPE': "chromium", 
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            "headless": False, 
            "channel": "chrome", 
            # FIXED: Changed from camelCase to snake_case for Python
            "ignore_default_args": ["--enable-automation"], 
            "args": [
                "--disable-blink-features=AutomationControlled", 
            ]
        },
        
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url, 
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        # Waits up to 20 seconds for the menu to appear on screen
                        PageMethod("wait_for_selector", "div.mp-level", timeout=20000)
                    ]
                } 
            )

    def parse(self, response):
        menu_links = response.css('div.mp-level ul li a::attr(href)').getall()
        category_tiles = response.css('a.sync_heights::attr(href)').getall()
        all_potential_cats = set(menu_links + category_tiles)
        
        for link in all_potential_cats:
            yield scrapy.Request(
                url=link, 
                callback=self.parse, 
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        # Wait for the page content to load
                        PageMethod("wait_for_selector", "div.breadcrumbs", timeout=15000)
                    ]
                }
            )

        product_links = response.css('li.mix a.product_lightbox::attr(href)').getall()
        for p_link in product_links:
            yield scrapy.Request(
                url=p_link, 
                callback=self.parse_product_details, 
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        # Wait for the product image gallery to load
                        PageMethod("wait_for_selector", ".product_gallery", timeout=15000)
                    ]
                }
            )

    def parse_product_details(self, response):
        image_link = response.css('.product_gallery a.zoom::attr(href)').get()
        
        mfr = None
        json_data = response.xpath('//script[@type="application/ld+json"]/text()').get()
        if json_data:
            try:
                data = json.loads(json_data)
                mfr = data.get('sku') or data.get('mpn')
            except:
                pass

        overview_texts = response.xpath('//div[contains(@class, "product_description")]//text()[not(ancestor::script) and not(ancestor::style)]').getall()
        overview = " | ".join([t.strip() for t in overview_texts if t.strip()])

        def get_spec(name):
            lower_name = name.lower()
            xpath_query = f'//table//th[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{lower_name}")]/following-sibling::td//text()'
            val = response.xpath(xpath_query).get()
            return val.strip() if val else None

        yield {
            'product_url': response.url,
            'mfr': mfr,
            'image_link': image_link,
            'overview': overview,
            'material': get_spec('Material'),
            'pattern': get_spec('Pattern'),
            'length': get_spec('Length'),
            'width': get_spec('Width'),
            'height': get_spec('Height'),
            'volume': get_spec('Volume'),
            'diameter': get_spec('Diameter'),
            'color': get_spec('Color'),
            'ean_code': get_spec('EAN'),
            'barcode': get_spec('Barcode')
        }