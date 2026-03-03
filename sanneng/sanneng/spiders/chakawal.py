import scrapy
import csv


class ChakawalSpider(scrapy.Spider):
    name = "chakawal"
    allowed_domains = ["chakawal.com"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_data = []
        self.max_pages = 26
    
    def start_requests(self):
        # Start from page 1 to 26
        for page in range(1, self.max_pages + 1):
            if page == 1:
                url = "https://chakawal.com/product-tag/sanneng/"
            else:
                url = f"https://chakawal.com/product-tag/sanneng/page/{page}/"
            yield scrapy.Request(url, callback=self.parse, meta={'page': page})
    
    def parse(self, response):
        page = response.meta['page']
        self.logger.info(f"Scraping page {page}")
        
        # Extract product links from the listing page
        product_links = response.css('li.archive-product-container a[href*="/product/"]::attr(href)').getall()
        
        # Deduplicate links (sometimes they appear twice)
        product_links = list(set(product_links))
        
        self.logger.info(f"Found {len(product_links)} products on page {page}")
        
        for link in product_links:
            if link:
                yield scrapy.Request(link, callback=self.parse_product)
    
    def parse_product(self, response):
        product = {}
        
        # SKU (MFR) - most important field
        sku = response.css('span.sku::text').get()
        if sku:
            product['sku'] = sku.strip()
        else:
            product['sku'] = 'N/A'
        
        # Product name
        name = response.css('h1.product_title::text').get() or \
               response.css('h1::text').get()
        product['name'] = name.strip() if name else 'N/A'
        
        # Image link - get the highest quality image
        image = response.css('div.woocommerce-product-gallery__image a::attr(href)').get() or \
                response.css('div.woocommerce-product-gallery__image img::attr(src)').get()
        product['image_link'] = image if image else 'N/A'
        
        # Overview/Description
        description = response.css('div.woocommerce-product-details__short-description *::text').getall()
        if not description:
            description = response.css('div.product-short-description *::text').getall()
        product['overview'] = ' '.join([d.strip() for d in description if d.strip()]) if description else 'N/A'
        
        # Categories
        categories = response.css('span.posted_in a::text').getall()
        product['categories'] = ', '.join(categories) if categories else 'N/A'
        
        # Tags
        tags = response.css('span.tagged_as a::text').getall()
        product['tags'] = ', '.join(tags) if tags else 'N/A'
        
        # Extract specifications from product details/attributes table
        specs = {}
        # WooCommerce additional information table
        for row in response.css('table.woocommerce-product-attributes tr'):
            label = row.css('th::text').get()
            value = row.css('td::text, td p::text').get()
            if label and value:
                specs[label.strip().lower().replace(':', '')] = value.strip()
        
        # Try to extract from various specification sections
        product['length'] = specs.get('length', specs.get('each length', 'N/A'))
        product['width'] = specs.get('width', specs.get('each width', 'N/A'))
        product['height'] = specs.get('height', specs.get('each height', 'N/A'))
        product['diameter'] = specs.get('diameter', 'N/A')
        product['volume'] = specs.get('volume', specs.get('capacity', 'N/A'))
        product['material'] = specs.get('material', 'N/A')
        product['color'] = specs.get('color', specs.get('colour', 'N/A'))
        product['pattern'] = specs.get('pattern', 'N/A')
        product['ean_code'] = specs.get('ean', specs.get('ean code', 'N/A'))
        product['barcode'] = specs.get('barcode', specs.get('upc', 'N/A'))
        
        # Product URL
        product['product_url'] = response.url
        product['source'] = 'chakawal.com'
        
        self.product_data.append(product)
        self.logger.info(f"Scraped: {product['name']} - SKU: {product['sku']}")
        
        yield product
    
    def closed(self, reason):
        if self.product_data:
            self.save_to_csv()
        self.logger.info(f"Spider closed. Total products scraped: {len(self.product_data)}")
    
    def save_to_csv(self):
        if not self.product_data:
            return
        
        fieldnames = [
            'sku', 'name', 'image_link', 'overview', 'length', 'width', 'height',
            'diameter', 'volume', 'material', 'color', 'pattern',
            'ean_code', 'barcode', 'categories', 'tags', 'product_url', 'source'
        ]
        
        filename = 'chakawal_products.csv'
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for product in self.product_data:
                    writer.writerow(product)
            self.logger.info(f"Data saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
