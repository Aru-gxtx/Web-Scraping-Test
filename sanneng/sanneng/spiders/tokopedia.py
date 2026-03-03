import scrapy
import csv
import json
import re


class TokopediaSpider(scrapy.Spider):
    name = "tokopedia"
    allowed_domains = ["www.tokopedia.com"]
    start_urls = ["https://www.tokopedia.com/search?st=&q=Sanneng&srp_component_id=02.01.00.00&srp_page_id=&srp_page_title=&navsource="]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_data = []
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 2,
    }
    
    def parse(self, response):
        self.logger.info("Parsing Tokopedia search results")
        
        # Extract product links
        product_links = response.css('a[href*="/tokopedia.com/"][href*="?"]::attr(href)').getall()
        
        # Filter for product pages
        product_links = [link for link in product_links if '/product/' in link or re.search(r'/[^/]+/[^/]+\?', link)]
        product_links = list(set(product_links))  # Deduplicate
        
        self.logger.info(f"Found {len(product_links)} products")
        
        for link in product_links[:50]:  # Limit to first 50 products
            if link.startswith('http'):
                yield scrapy.Request(link, callback=self.parse_product, dont_filter=True)
            else:
                yield scrapy.Request(response.urljoin(link), callback=self.parse_product, dont_filter=True)
    
    def parse_product(self, response):
        product = {}
        
        # Try to find SKU in the title or description
        title = response.css('h1::text, h1 span::text').get()
        if not title:
            title = response.css('meta[property="og:title"]::attr(content)').get()
        
        product['name'] = title.strip() if title else 'N/A'
        
        # Extract SKU from title (usually in format "- SKU" or "SKU:")
        sku_match = re.search(r'(SN\w+)', product['name'], re.I)
        if sku_match:
            product['sku'] = sku_match.group(1).upper()
        else:
            product['sku'] = 'N/A'
        
        # Image
        image = response.css('img[alt*="product"]::attr(src)').get() or \
                response.css('meta[property="og:image"]::attr(content)').get()
        product['image_link'] = image if image else 'N/A'
        
        # Overview/Description
        desc = response.css('div[data-testid="lblPDPDescriptionProduk"]::text').getall() or \
               response.css('meta[name="description"]::attr(content)').get()
        if isinstance(desc, list):
            product['overview'] = ' '.join([d.strip() for d in desc if d.strip()])
        else:
            product['overview'] = desc if desc else 'N/A'
        
        # Default values
        product['length'] = 'N/A'
        product['width'] = 'N/A'
        product['height'] = 'N/A'
        product['diameter'] = 'N/A'
        product['volume'] = 'N/A'
        product['material'] = 'N/A'
        product['color'] = 'N/A'
        product['pattern'] = 'N/A'
        product['ean_code'] = 'N/A'
        product['barcode'] = 'N/A'
        
        # Product URL
        product['product_url'] = response.url
        product['source'] = 'tokopedia.com'
        
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
            'ean_code', 'barcode', 'product_url', 'source'
        ]
        
        filename = 'tokopedia_products.csv'
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for product in self.product_data:
                    writer.writerow(product)
            self.logger.info(f"Data saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
