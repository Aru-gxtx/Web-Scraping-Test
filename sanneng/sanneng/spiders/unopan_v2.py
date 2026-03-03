import scrapy
import json
import re


class UnopanSpider(scrapy.Spider):
    name = "unopan_v2"
    allowed_domains = ["unopan.tw", "www.unopan.tw"]
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
    }
    
    def start_requests(self):
        # Unopan uses JavaScript - request with Playwright
        url = "https://www.unopan.tw/search?q=SANNENG"
        yield scrapy.Request(
            url,
            callback=self.parse,
            meta={'playwright': True}
        )
    
    def parse(self, response):
        self.logger.info(f"Parsing Unopan search - Status: {response.status}")
        
        # Extract product links
        product_links = response.css('a[href*="/product"]::attr(href)').getall()
        if not product_links:
            product_links = response.css('div.item a::attr(href)').getall()
        
        product_links = [response.urljoin(link) for link in product_links]
        product_links = list(set(product_links))[:50]
        
        self.logger.info(f"Found {len(product_links)} products")
        
        for link in product_links:
            yield scrapy.Request(
                link,
                callback=self.parse_product,
                meta={'playwright': True}
            )
    
    def parse_product(self, response):
        try:
            product = {}
            
            # Get title
            title = response.css('h1::text').get() or \
                   response.xpath('//h1/text()').get() or ''
            product['name'] = title.strip() if title else 'N/A'
            
            # Extract SKU from title
            sku_match = re.search(r'(SN\d+)', product['name'], re.I)
            if sku_match:
                product['sku'] = sku_match.group(1).upper()
            else:
                # Try JSON-LD
                json_ld = response.css('script[type="application/ld+json"]::text').get()
                if json_ld:
                    try:
                        data = json.loads(json_ld)
                        product['sku'] = data.get('sku', 'N/A')
                    except:
                        product['sku'] = 'N/A'
                else:
                    product['sku'] = 'N/A'
            
            # Image
            image = response.css('img[alt*="product"]::attr(src)').get()
            if not image:
                image = response.css('meta[property="og:image"]::attr(content)').get()
            product['image_link'] = image if image else 'N/A'
            
            # Description
            description = response.css('div.description::text').getall()
            product['overview'] = ' '.join([d.strip() for d in description if d.strip()]) if description else 'N/A'
            
            # Extract specifications
            spec_mapping = {
                '長度': 'length',
                '寬度': 'width',
                '高度': 'height',
                '直徑': 'diameter',
                '容量': 'volume',
                '材料': 'material',
                '顏色': 'color',
                '花紋': 'pattern',
                'EAN': 'ean_code',
                '條碼': 'barcode',
            }
            
            specs = {}
            for row in response.css('tr'):
                key_cell = row.css('td:first-child::text').get()
                val_cell = row.css('td:last-child::text').get()
                if key_cell and val_cell:
                    specs[key_cell.strip()] = val_cell.strip()
            
            # Map specs
            for zh_key, en_key in spec_mapping.items():
                product[en_key] = specs.get(zh_key, 'N/A')
            
            # Set defaults for missing fields
            for field in ['length', 'width', 'height', 'diameter', 'volume', 'material', 'color', 'pattern', 'ean_code', 'barcode', 'upc']:
                if field not in product or product[field] == '':
                    product[field] = 'N/A'
            
            product['upc'] = specs.get('UPC', 'N/A')
            product['product_url'] = response.url
            product['source'] = 'unopan.tw'
            
            self.logger.info(f"Scraped: {product.get('sku')} - {product.get('name')}")
            yield product
            
        except Exception as e:
            self.logger.error(f"Error parsing product {response.url}: {e}")
