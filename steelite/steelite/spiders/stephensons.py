import scrapy
import csv
from scrapy_playwright.page import PageMethod


class StephensonsSpider(scrapy.Spider):
    name = "stephensons"
    allowed_domains = ["www.stephensons.com"]
    start_urls = ["https://www.stephensons.com/catering-crockery/steelite-crockery"]
    csv_filename = "stephensons_products.csv"

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'DOWNLOAD_DELAY': 2,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler': 585,
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_data = []

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_products,
                meta={'playwright': True}
            )

    def parse_products(self, response):
        # Find all product links on the page (rendered by JavaScript)
        product_links = response.css('a.product-item-photo::attr(href)').getall()
        self.logger.info(f"Found {len(product_links)} product links on page")
        
        for product_url in product_links:
            if product_url:
                yield scrapy.Request(
                    url=product_url,
                    callback=self.parse_product_details,
                    meta={'playwright': True}
                )

        # Check for pagination
        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            yield scrapy.Request(
                url=next_page,
                callback=self.parse_products,
                meta={'playwright': True}
            )

    def parse_product_details(self, response):
        image_link = response.css('meta[property="og:image"]::attr(content)').get()
        
        overview_texts = response.xpath('//div[contains(@class, "product attribute description")]//div[@class="value"]//text()[not(ancestor::style) and not(ancestor::script)]').getall()
        overview = " | ".join([text.strip() for text in overview_texts if text.strip()])
        
        mfr = response.css('div.product.attribute.sku div.value::text').get()
        if not mfr:
            mfr = response.css('[itemprop="sku"]::text, [itemprop="mpn"]::text').get()
        
        product_name = response.css('h1.page-title::text').get() or "N/A"
        if isinstance(product_name, str):
            product_name = product_name.strip()
        
        def get_spec(spec_name):
            lower_spec = spec_name.lower()
            xpath_query = f'//table//th[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{lower_spec}")]/following-sibling::td//text()'
            texts = response.xpath(xpath_query).getall()
            cleaned_texts = [t.strip() for t in texts if t.strip() and t.strip() != '\xa0']
            result = ", ".join(cleaned_texts)
            return result if result else "N/A"

        product = {
            'name': product_name,
            'item_sku': mfr.strip() if mfr else "N/A",
            'model_number': "N/A",
            'manufacturer': mfr.strip() if mfr else "N/A",
            'image_link': image_link or "N/A",
            'overview': overview or "N/A",
            'material': get_spec('Material'),
            'color': get_spec('Color'),
            'pattern': get_spec('Pattern'),
            'length': get_spec('Length'),
            'width': get_spec('Width'),
            'height': get_spec('Height'),
            'volume_capacity': get_spec('Volume'),
            'diameter': get_spec('Diameter'),
            'country_of_origin': "N/A",
            'upc_barcode': get_spec('Barcode'),
            'ean_code': get_spec('EAN'),
            'hazmat': "N/A",
            'oversize': "N/A",
            'marketplace_uom': "N/A",
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