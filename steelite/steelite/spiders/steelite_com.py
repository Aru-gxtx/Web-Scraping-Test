import scrapy
import csv
import json


class SteeliteComSpider(scrapy.Spider):
    name = "steelite_com"
    allowed_domains = ["steelite.com"]
    csv_filename = "steelite_com_products.csv"
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 1,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_data = []
    
    def start_requests(self):
        # Try multiple entry points
        urls = [
            "https://www.steelite.com/search/?cgid=dinnerware",
            "https://www.steelite.com/search/?cgid=serveware",
            "https://www.steelite.com/search/?cgid=drinkware",
            "https://www.steelite.com/search/?q=steelite",
        ]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse_listing, dont_filter=True)
    
    def parse_listing(self, response):
        # Find product links with multiple selectors
        product_links = (
            response.css('a.product-tile::attr(href)').getall() or
            response.css('a[class*="product"]::attr(href)').getall() or
            response.css('div.product a::attr(href)').getall()
        )
        
        self.logger.info(f"Found {len(product_links)} product links")
        
        for link in product_links[:200]:  # Limit to prevent too many requests
            if link:
                yield scrapy.Request(response.urljoin(link), callback=self.parse_product)
        
        # Pagination
        next_page = response.css('a.pagination-next::attr(href), a[rel="next"]::attr(href)').get()
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse_listing)
    
    def parse_product(self, response):
        # Extract data with fallbacks
        name = (
            response.css('h1.product-name::text').get() or
            response.css('h1::text').get() or
            response.css('[itemprop="name"]::text').get() or
            "N/A"
        ).strip()
        
        # SKU/Model
        sku = (
            response.css('.product-id::text').get() or
            response.css('[itemprop="sku"]::text').get() or
            response.css('.product-number::text').get() or
            "N/A"
        ).strip()
        
        # Image
        image = (
            response.css('.product-image img::attr(src)').get() or
            response.css('[itemprop="image"]::attr(href)').get() or
            response.css('img.primary-image::attr(src)').get() or
            "N/A"
        )
        if image and not image.startswith('http'):
            image = response.urljoin(image)
        
        # Description
        desc_parts = response.css('.product-description ::text, .description ::text').getall()
        description = ' '.join([t.strip() for t in desc_parts if t.strip()])[:500]
        
        product = {
            'name': name,
            'item_sku': sku,
            'model_number': sku,
            'manufacturer': sku,
            'image_link': image,
            'overview': description or "N/A",
            'material': "N/A",
            'color': "N/A",
            'pattern': "N/A",
            'length': "N/A",
            'width': "N/A",
            'height': "N/A",
            'volume_capacity': "N/A",
            'diameter': "N/A",
            'country_of_origin': "N/A",
            'upc_barcode': "N/A",
            'ean_code': "N/A",
            'hazmat': "N/A",
            'oversize': "N/A",
            'marketplace_uom': "N/A",
            'product_url': response.url,
        }
        
        self.product_data.append(product)
        self.logger.info(f"Scraped: {name[:50]}")
        yield product
    
    def closed(self, reason):
        if not self.product_data:
            self.logger.warning("No products scraped")
            return
        
        fieldnames = [
            'name', 'item_sku', 'model_number', 'manufacturer',
            'image_link', 'overview', 'material', 'color', 'pattern',
            'length', 'width', 'height', 'volume_capacity', 'diameter',
            'country_of_origin', 'upc_barcode', 'ean_code',
            'hazmat', 'oversize', 'marketplace_uom', 'product_url'
        ]
        
        try:
            with open(self.csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.product_data)
            self.logger.info(f"✓ Saved {len(self.product_data)} products to {self.csv_filename}")
        except Exception as e:
            self.logger.error(f"Error saving CSV: {e}")
