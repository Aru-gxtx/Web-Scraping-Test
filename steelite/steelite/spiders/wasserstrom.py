import scrapy
from scrapy.crawler import CrawlerProcess
import csv


class WasserstromSpider(scrapy.Spider):
    name = "wasserstrom"
    allowed_domains = ["www.wasserstrom.com"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://www.wasserstrom.com/restaurant-supplies-equipment/SearchDisplay"
        self.page_size = 100
        self.max_pages = 30
        self.product_data = []
    
    def start_requests(self):
        for page in range(1, self.max_pages + 1):
            begin_index = (page - 1) * self.page_size
            url = f"{self.base_url}?searchTerm=steelite&beginIndex={begin_index}&pageSize={self.page_size}&storeId=10051&catalogId=3074457345616677089&langId=-1"
            yield scrapy.Request(url, callback=self.parse_listing, meta={'page': page})
    
    def parse_listing(self, response):
        page = response.meta['page']
        self.logger.info(f"Scraping page {page}")
        
        product_links = response.css('div.product a[id*="catalogEntry"]::attr(href)').getall()
        
        # Fallback selector if primary doesn't work
        if not product_links:
            product_links = response.css('li .product_name a::attr(href)').getall()
        
        # Another fallback
        if not product_links:
            product_links = response.css('a[title*="Steelite"]::attr(href)').getall()
        
        self.logger.info(f"Found {len(product_links)} products on page {page}")
        
        if not product_links:
            self.logger.warning(f"No products found on page {page}")
        
        for link in product_links:
            if link and not link.startswith('javascript'):
                # Handle relative URLs
                product_url = response.urljoin(link)
                yield scrapy.Request(product_url, callback=self.parse_product, 
                                   errback=self.errback_parse_product)
    
    def parse_product(self, response):
        product = {}
        
        # Product name - try multiple selectors
        product['name'] = (
            response.css('h1 span::text').get() or
            response.css('h1::text').get() or
            response.css('[itemprop="name"]::text').get() or
            response.css('div.product_name a::text').get() or
            'N/A'
        )
        if product['name']:
            product['name'] = product['name'].strip()
        
        sku_spans = response.css('span.sku')
        product['item_sku'] = 'N/A'
        product['model_number'] = 'N/A'
        product['manufacturer'] = 'N/A'
        
        for span in sku_spans:
            # Get all text content from the span
            text_content = span.css('::text, *::text').getall()
            full_text = ' '.join([t.strip() for t in text_content if t.strip()])
            
            if 'Item #' in full_text:
                # Extract the number after "Item #:"
                item_num = full_text.split('Item #')[-1].replace(':', '').strip()
                product['item_sku'] = item_num
                product['manufacturer'] = item_num  # Manufacturer is the Item #
            elif 'Model #' in full_text:
                # Extract the model number
                model_num = full_text.split('Model #')[-1].replace(':', '').strip()
                product['model_number'] = model_num
        
        # Image link - get first high-quality image
        image_link = (
            response.css('img[itemprop="image"]::attr(src)').get() or
            response.css('picture img::attr(src)').get() or
            response.css('div.image img::attr(src)').get()
        )
        product['image_link'] = image_link if image_link else 'N/A'
        
        # Overview/Description - get first paragraph or full description
        description_text = response.css('div.longDescription::text').getall()
        if not description_text:
            description_text = response.css('div.longDescription p::text').getall()
        
        product['overview'] = ' '.join([t.strip() for t in description_text if t.strip()]) if description_text else 'N/A'
        if len(product['overview']) > 500:
            product['overview'] = product['overview'][:500] + '...'
        
        # Parse specifications from widget_product_compare
        specs = {}
        rows = response.css('div.widget_product_compare div.row')
        
        for row in rows:
            heading = row.css('div.heading::text').get()
            item = row.css('div.item::text').get()
            
            if heading and item:
                heading = heading.strip().lower().replace('&nbsp;', '').strip()
                item = item.strip()
                specs[heading] = item
        
        # Extract specific fields from specs
        product['material'] = specs.get('material', 'N/A')
        product['color'] = specs.get('color', 'N/A')
        product['pattern'] = specs.get('pattern', 'N/A')
        product['length'] = specs.get('each length', 'N/A')
        product['width'] = specs.get('each width', 'N/A')
        product['height'] = specs.get('each height', 'N/A')
        product['volume_capacity'] = specs.get('volume capacity', 'N/A')
        product['diameter'] = specs.get('diameter', 'N/A')
        product['country_of_origin'] = specs.get('country of origin', 'N/A')
        
        # EAN Code and UPC (barcode)
        product['upc_barcode'] = specs.get('upc', 'N/A')
        product['ean_code'] = specs.get('ean', 'N/A')
        
        # Additional specs that might be useful
        product['hazmat'] = specs.get('hazmat', 'N/A')
        product['oversize'] = specs.get('oversize', 'N/A')
        product['marketplace_uom'] = specs.get('marketplace uom', 'N/A')
        
        # Product URL
        product['product_url'] = response.url
        
        self.product_data.append(product)
        self.logger.info(f"Scraped product: {product['name']}")
        
        yield product
    
    def closed(self, reason):
        if self.product_data:
            self.save_to_csv()
        self.logger.info(f"Spider closed. Total products scraped: {len(self.product_data)}")
    
    def errback_parse_product(self, failure):
        self.logger.error(f"Error fetching product: {failure.request.url}")
        self.logger.error(f"Error: {failure.value}")
    
    def save_to_csv(self):
        if not self.product_data:
            return
        
        # Define CSV header
        fieldnames = [
            'name', 'item_sku', 'model_number', 'manufacturer', 'image_link', 'overview',
            'material', 'color', 'pattern', 'length', 'width', 'height',
            'volume_capacity', 'diameter', 'country_of_origin',
            'upc_barcode', 'ean_code', 'hazmat', 'oversize',
            'marketplace_uom', 'product_url'
        ]
        
        filename = 'wasserstrom_products.csv'
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for product in self.product_data:
                    writer.writerow(product)
            self.logger.info(f"Data saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
