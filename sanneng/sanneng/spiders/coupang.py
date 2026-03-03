import scrapy
import csv
import re


class CoupangSpider(scrapy.Spider):
    name = "coupang"
    allowed_domains = ["www.tw.coupang.com"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_data = []
        self.max_pages = 27
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 2,
    }
    
    def start_requests(self):
        for page in range(1, self.max_pages + 1):
            url = f"https://www.tw.coupang.com/search?q=SaNNeNg&traceId=mm0bk8qg&channel=user&page={page}"
            yield scrapy.Request(url, callback=self.parse, meta={'page': page})
    
    def parse(self, response):
        page = response.meta['page']
        self.logger.info(f"Scraping page {page}")
        
        # Extract product links
        product_links = response.css('li.ProductUnit_productUnit__Qd6sv a::attr(href)').getall()
        
        if not product_links:
            product_links = response.css('a[href*="/products/"]::attr(href)').getall()
        
        # Make URLs absolute
        product_links = [response.urljoin(link) if not link.startswith('http') else link for link in product_links]
        product_links = list(set(product_links))  # Deduplicate
        
        self.logger.info(f"Found {len(product_links)} products on page {page}")
        
        for link in product_links:
            yield scrapy.Request(link, callback=self.parse_product, dont_filter=True)
    
    def parse_product(self, response):
        product = {}
        
        # Product name
        name = response.css('h1.prod-buy-header__title::text').get() or \
               response.css('h1::text').get() or \
               response.css('meta[property="og:title"]::attr(content)').get()
        product['name'] = name.strip() if name else 'N/A'
        
        # Extract SKU from title
        sku_match = re.search(r'(SN\w+)', product['name'], re.I)
        if sku_match:
            product['sku'] = sku_match.group(1).upper()
        else:
            # Try from product code
            sku_el = response.css('span:contains("型號")::text, span:contains("品號")::text').get()
            if sku_el:
                sku_match = re.search(r'(SN\w+)', sku_el, re.I)
                if sku_match:
                    product['sku'] = sku_match.group(1).upper()
                else:
                    product['sku'] = 'N/A'
            else:
                product['sku'] = 'N/A'
        
        # Image
        image = response.css('img.prod-image__detail::attr(src)').get() or \
                response.css('meta[property="og:image"]::attr(content)').get()
        product['image_link'] = image if image else 'N/A'
        
        # Overview/Description
        desc = response.css('div.prod-description__content *::text').getall() or \
               response.css('meta[name="description"]::attr(content)').get()
        if isinstance(desc, list):
            product['overview'] = ' '.join([d.strip() for d in desc if d.strip()])[:500]
        else:
            product['overview'] = desc if desc else 'N/A'
        
        # Try to extract specifications
        specs = {}
        spec_rows = response.css('table.prod-attr-table tr, div.spec-item')
        for row in spec_rows:
            label = row.css('th::text, .spec-label::text').get()
            value = row.css('td::text, .spec-value::text').get()
            if label and value:
                specs[label.strip().lower()] = value.strip()
        
        product['length'] = specs.get('length', specs.get('長度', 'N/A'))
        product['width'] = specs.get('width', specs.get('寬度', 'N/A'))
        product['height'] = specs.get('height', specs.get('高度', 'N/A'))
        product['diameter'] = specs.get('diameter', specs.get('直徑', 'N/A'))
        product['volume'] = specs.get('volume', specs.get('容量', 'N/A'))
        product['material'] = specs.get('material', specs.get('材質', 'N/A'))
        product['color'] = specs.get('color', specs.get('顏色', 'N/A'))
        product['pattern'] = specs.get('pattern', 'N/A')
        product['ean_code'] = specs.get('ean', 'N/A')
        product['barcode'] = specs.get('barcode', specs.get('upc', 'N/A'))
        
        # Product URL
        product['product_url'] = response.url
        product['source'] = 'coupang.tw'
        
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
        
        filename = 'coupang_products.csv'
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for product in self.product_data:
                    writer.writerow(product)
            self.logger.info(f"Data saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
