import scrapy
import csv
import re
import json


class SannengvietnamSpider(scrapy.Spider):
    name = "sannengvietnam"
    allowed_domains = ["sannengvietnam.com"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_data = []
        self.max_pages = 4
    
    def start_requests(self):
        for page in range(1, self.max_pages + 1):
            url = f"https://sannengvietnam.com/collections/all?page={page}"
            yield scrapy.Request(url, callback=self.parse, meta={'page': page})
    
    def parse(self, response):
        page = response.meta['page']
        self.logger.info(f"Scraping page {page}")
        
        # Extract product links
        product_links = response.css('div.product-block a[href*="/products/"]::attr(href)').getall()
        
        # Make sure URLs are absolute
        product_links = [response.urljoin(link) for link in product_links]
        product_links = list(set(product_links))  # Deduplicate
        
        self.logger.info(f"Found {len(product_links)} products on page {page}")
        
        for link in product_links:
            yield scrapy.Request(link, callback=self.parse_product)
    
    def parse_product(self, response):
        product = {}
        
        # SKU from meta description or title
        meta_desc = response.css('meta[name="description"]::attr(content)').get()
        if meta_desc and 'Mã sản phẩm:' in meta_desc:
            sku_match = re.search(r'Mã sản phẩm:\s*(SN\w+)', meta_desc)
            if sku_match:
                product['sku'] = sku_match.group(1)
        
        if 'sku' not in product or not product.get('sku'):
            # Try from URL - match SN, UN, or other 2-letter + number patterns
            url_sku = re.search(r'([a-z]{2}\d+\w*)', response.url, re.I)
            if url_sku:
                product['sku'] = url_sku.group(1).upper()
            else:
                product['sku'] = 'N/A'
        
        # Product name
        name = response.css('h1.title::text').get() or \
               response.css('h1::text').get()
        product['name'] = name.strip() if name else 'N/A'
        
        # Image link - primary selector with meta fallbacks
        image = response.css('div.large-image img::attr(src)').get()
        if not image:
            image = response.css('div.product-photos img::attr(src)').get()
        if not image:
            image = response.css('img.product-featured-media::attr(src)').get()
        if not image:
            image = response.css('meta[property="og:image"]::attr(content)').get()
        if not image:
            image = response.css('meta[name="twitter:image"]::attr(content)').get()

        if image and image.startswith('//'):
            image = 'https:' + image
        elif image and image.startswith('/'):
            image = response.urljoin(image)

        product['image_link'] = image if image else 'N/A'
        
        # Overview - from meta description
        product['overview'] = meta_desc if meta_desc else 'N/A'
        
        # Extract dimensions and material from description
        if meta_desc:
            # Size extraction: 60x40x20cm
            size_match = re.search(r'Kích thước:\s*(\d+)x(\d+)x(\d+)\s*cm', meta_desc)
            if size_match:
                product['length'] = f"{size_match.group(1)}cm"
                product['width'] = f"{size_match.group(2)}cm"
                product['height'] = f"{size_match.group(3)}cm"
            else:
                product['length'] = 'N/A'
                product['width'] = 'N/A'
                product['height'] = 'N/A'
            
            # Material extraction
            material_match = re.search(r'Chất liệu:\s*([^-]+)', meta_desc)
            if material_match:
                product['material'] = material_match.group(1).strip()
            else:
                product['material'] = 'N/A'
        else:
            product['length'] = 'N/A'
            product['width'] = 'N/A'
            product['height'] = 'N/A'
            product['material'] = 'N/A'
        
        product['diameter'] = 'N/A'
        product['volume'] = 'N/A'
        product['color'] = 'N/A'
        product['pattern'] = 'N/A'
        product['ean_code'] = 'N/A'
        product['barcode'] = 'N/A'
        
        # Product URL
        product['product_url'] = response.url
        product['source'] = 'sannengvietnam.com'
        
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
        
        filename = 'sannengvietnam_products.csv'
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for product in self.product_data:
                    writer.writerow(product)
            self.logger.info(f"Data saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
