import scrapy
import csv
import json
import re


class UnopanSpider(scrapy.Spider):
    name = "unopan"
    allowed_domains = ["www.unopan.tw"]
    start_urls = ["https://www.unopan.tw/search?q=SANNENG+"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_data = []
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    def parse(self, response):
        self.logger.info("Parsing product listing page")
        product_links = response.css('div.item a[href*="/products/"]::attr(href)').getall()
        
        if not product_links:
            product_links = response.css('a.product_image::attr(href)').getall()
        
       # Make URLs absolute
        product_links = [response.urljoin(link) for link in product_links]
        product_links = list(set(product_links))  # Deduplicate
        
        self.logger.info(f"Found {len(product_links)} products")
        
        for link in product_links:
            yield scrapy.Request(link, callback=self.parse_product)
    
    def parse_product(self, response):
        product = {}
        
        # SKU from JSON-LD
        json_ld = response.css('script[type="application/ld+json"]::text').get()
        if json_ld:
            try:
                data = json.loads(json_ld)
                if isinstance(data, dict) and 'sku' in data:
                    product['sku'] = data.get('sku', 'N/A')
                else:
                    product['sku'] = 'N/A'
            except:
                product['sku'] = 'N/A'
        else:
            product['sku'] = 'N/A'
        
        # Fallback: Extract SKU from URL or title
        if product['sku'] == 'N/A':
            url_sku = re.search(r'/products/(sn\w+)', response.url, re.I)
            if url_sku:
                product['sku'] = url_sku.group(1).upper()
        
        # Product name - try multiple selectors
        name = response.css('h1.product_title::text').get() or \
               response.css('h1::text').get() or \
               response.css('meta[property="og:title"]::attr(content)').get()
        product['name'] = name.strip() if name else 'N/A'
        
        # Image link
        image = response.css('meta[property="og:image"]::attr(content)').get() or \
                response.css('div.product_image img::attr(src)').get()
        product['image_link'] = image if image else 'N/A'
        
        # Overview/Description
        desc = response.css('meta[name="description"]::attr(content)').get() or \
               response.css('div.product_description::text').getall()
        if isinstance(desc, list):
            product['overview'] = ' '.join([d.strip() for d in desc if d.strip()])
        else:
            product['overview'] = desc if desc else 'N/A'
        
        specs = {}
        for row in response.css('table tr, div.spec-row, div.description'):
            label_text = row.css('th::text, .label::text').get()
            value_text = row.css('td::text, .value::text').get()
            if label_text and value_text:
                specs[label_text.strip().lower()] = value_text.strip()
        
        product['length'] = specs.get('length', specs.get('長度', 'N/A'))
        product['width'] = specs.get('width', specs.get('寬度', 'N/A'))
        product['height'] = specs.get('height', specs.get('高度', 'N/A'))
        product['diameter'] = specs.get('diameter', specs.get('直徑', 'N/A'))
        product['volume'] = specs.get('volume', specs.get('capacity', specs.get('容量', 'N/A')))
        product['material'] = specs.get('material', specs.get('材質', 'N/A'))
        product['color'] = specs.get('color', specs.get('顏色', 'N/A'))
        product['pattern'] = specs.get('pattern', 'N/A')
        product['ean_code'] = specs.get('ean', 'N/A')
        product['barcode'] = specs.get('barcode', specs.get('upc', 'N/A'))
        
        # Product URL
        product['product_url'] = response.url
        product['source'] = 'unopan.tw'
        
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
        
        filename = 'unopan_products.csv'
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for product in self.product_data:
                    writer.writerow(product)
            self.logger.info(f"Data saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
