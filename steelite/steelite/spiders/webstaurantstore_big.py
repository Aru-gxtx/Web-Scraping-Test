import scrapy
import csv


class WebstaurantStoreBigSpider(scrapy.Spider):
    name = "webstaurantstore_big"
    allowed_domains = ["www.webstaurantstore.com"]
    csv_filename = "webstaurantstore_big_products.csv"
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'DOWNLOAD_DELAY': 2,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_data = []
        self.seen_urls = set()
    
    def start_requests(self):
        # Multiple search variations
        base_url = "https://www.webstaurantstore.com/search/steelite.html?page={}"
        for page in range(1, 15):  # First 15 pages = ~750 products
            yield scrapy.Request(
                base_url.format(page),
                callback=self.parse_listing,
                meta={'page': page}
            )
    
    def parse_listing(self, response):
        # Extract product links - WebstaurantStore uses data-testid="itemLink"
        product_links = response.css('a[data-testid="itemLink"]::attr(href)').getall()
        
        if not product_links:
            # Fallback selectors
            product_links = response.css('a[href*="/item/"]::attr(href)').getall()
            product_links = [l for l in product_links if '/item/' in l]
        
        self.logger.info(f"Page {response.meta.get('page')}: Found {len(product_links)} products")
        
        for link in product_links[:50]:  # Limit per page
            url = response.urljoin(link)
            if url not in self.seen_urls and '/item/' in url:
                self.seen_urls.add(url)
                yield scrapy.Request(url, callback=self.parse_product)
    
    def parse_product(self, response):
        # Extract product name
        name = response.css('h1::text').get()
        if not name:
            name = response.xpath('//h1/text()').get()
        name = name.strip() if name else "N/A"
        
        # Extract manufacturer number
        mfr = response.css('span[data-testid="product-detail-heading-vendor-number"] span.uppercase::text').get()
        item_num = mfr.strip() if mfr else "N/A"
        
        # Extract image
        image = response.css('img#GalleryImage::attr(src)').get()
        if not image:
            image = response.css('meta[property="og:image"]::attr(content)').get()
        image = response.urljoin(image) if image else "N/A"
        
        # Extract overview from highlights
        overview_bullets = response.css('div[data-testid="highlights-meta-side-section"] ul li span::text').getall()
        desc = " | ".join([bullet.strip() for bullet in overview_bullets if bullet.strip()])
        
        # Helper function for specs
        def get_spec(spec_name):
            xpath = f'//dt[contains(., "{spec_name}")]/following-sibling::dd[1]//text()'
            texts = response.xpath(xpath).getall()
            return ", ".join([t.strip() for t in texts if t.strip()]) or "N/A"
        
        product = {
            'name': name,
            'item_sku': item_num,
            'model_number': item_num,
            'manufacturer': item_num,
            'image_link': image,
            'overview': desc or "N/A",
            'material': get_spec('Material'),
            'color': get_spec('Color'),
            'pattern': get_spec('Pattern'),
            'length': get_spec('Length'),
            'width': get_spec('Width'),
            'height': get_spec('Height'),
            'volume_capacity': get_spec('Capacity'),
            'diameter': get_spec('Diameter'),
            'country_of_origin': get_spec('Country of Origin'),
            'upc_barcode': "N/A",
            'ean_code': "N/A",
            'hazmat': "N/A",
            'oversize': "N/A",
            'marketplace_uom': "N/A",
            'product_url': response.url,
        }
        
        self.product_data.append(product)
        self.logger.info(f"✓ {name[:50]}")
        yield product
    
    def closed(self, reason):
        if not self.product_data:
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
            self.logger.info(f"Saved {len(self.product_data)} products to {self.csv_filename}")
        except Exception as e:
            self.logger.error(f"Error saving CSV: {e}")
