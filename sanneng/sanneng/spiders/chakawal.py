import scrapy


class ChakawalSpider(scrapy.Spider):
    name = "chakawal"
    allowed_domains = ["chakawal.com"]
    custom_settings = {
        'DOWNLOAD_DELAY': 4,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
    }
    
    def start_requests(self):
        for page in range(1, 5):  # Test with 4 pages
            if page == 1:
                url = "https://chakawal.com/product-tag/sanneng/"
            else:
                url = f"https://chakawal.com/product-tag/sanneng/page/{page}/"
            
            yield scrapy.Request(
                url, 
                callback=self.parse,
                meta={
                    'page': page,
                    'playwright': True,  # Enable browser rendering for this site
                    'playwright_include_page': False,
                },
                headers={'Referer': 'https://chakawal.com/'}
            )
    
    def parse(self, response):
        page = response.meta.get('page', 1)
        self.logger.info(f"Scraping page {page} - Status: {response.status}")
        
        # After JS rendering, selectors should work
        product_links = response.css('a.product-link::attr(href)').getall()
        if not product_links:
            product_links = response.css('a[href*="/product/"]::attr(href)').getall()
        
        product_links = list(set(link for link in product_links if '/product/' in link))
        self.logger.info(f"Found {len(product_links)} products on page {page}")
        
        for link in product_links:
            yield scrapy.Request(
                link,
                callback=self.parse_product,
                headers={'Referer': response.url}
            )

    def extract_image(self, response):
        selectors = [
            'img.wp-post-image::attr(src)',
            'img.wp-post-image::attr(data-src)',
            'figure.woocommerce-product-gallery__wrapper img::attr(src)',
            'meta[property="og:image"]::attr(content)',
            'meta[name="twitter:image"]::attr(content)',
        ]
        for selector in selectors:
            image = response.css(selector).get()
            if image:
                return response.urljoin(image)
        return 'N/A'
    
    def parse_product(self, response):
        try:
            product = {}
            
            sku = response.css('span.sku::text').get()
            product['sku'] = sku.strip() if sku else 'N/A'
            
            name = response.css('h1.product_title::text').get()
            product['name'] = name.strip() if name else 'N/A'
            
            product['image_link'] = self.extract_image(response)
            
            desc = response.css('div.woocommerce-product-details__short-description::text').getall()
            product['overview'] = ' '.join([d.strip() for d in desc if d.strip()]) if desc else 'N/A'
            
            specs = {}
            for row in response.css('tr'):
                th = row.css('th::text').get()
                td = row.css('td::text').get()
                if th and td:
                    specs[th.strip()] = td.strip()
            
            product['length'] = specs.get('Length', 'N/A')
            product['width'] = specs.get('Width', 'N/A')
            product['height'] = specs.get('Height', 'N/A')
            product['diameter'] = specs.get('Diameter', 'N/A')
            product['volume'] = specs.get('Volume', 'N/A')
            product['material'] = specs.get('Material', 'N/A')
            product['color'] = specs.get('Color', 'N/A')
            product['pattern'] = specs.get('Pattern', 'N/A')
            product['ean_code'] = specs.get('EAN', 'N/A')
            product['barcode'] = specs.get('Barcode', 'N/A')
            product['upc'] = specs.get('UPC', 'N/A')
            
            product['product_url'] = response.url
            product['source'] = 'chakawal.com'
            
            self.logger.info(f"Scraped: {product.get('sku')} - {product.get('name')}")
            yield product
            
        except Exception as e:
            self.logger.error(f"Error parsing {response.url}: {e}")
