import scrapy
import csv
import json


class WebstaurantStoreVendorSpider(scrapy.Spider):
    name = "webstaurantstore_vendor"
    allowed_domains = ["www.webstaurantstore.com"]
    start_urls = ["https://www.webstaurantstore.com/vendor/steelite-international.html"]
    csv_filename = "webstaurantstore_vendor_products.csv"

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 1,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_data = []
        self.seen_urls = set()

    def parse(self, response):
        # Extract JSON from Hypernova script tag (same as original webstaurantstore.py)
        script_text = response.css('script[data-hypernova-key="BrandGroupPage"]::text').get()
        
        if script_text:
            clean_json = script_text.strip()[4:-3]
            try:
                data = json.loads(clean_json)
                
                def extract_categories(obj):
                    if isinstance(obj, dict):
                        if 'url' in obj and 'description' in obj and 'name' in obj:
                            yield {
                                'title': obj.get('name'),
                                'description': obj.get('description'),
                                'url': response.urljoin(obj.get('url'))
                            }
                        else:
                            for value in obj.values():
                                yield from extract_categories(value)
                    elif isinstance(obj, list):
                        for item in obj:
                            yield from extract_categories(item)
                
                category_count = 0
                for category in extract_categories(data):
                    if category_count >= 5:  # LIMIT: Test with first 5 categories
                        break
                    if category['url'] not in self.seen_urls:
                        self.seen_urls.add(category['url'])
                        category_count += 1
                        yield scrapy.Request(
                            url=category['url'],
                            callback=self.parse_category,
                            meta={'category_name': category['title']}
                        )
                
                self.logger.info(f"Found {category_count} categories from JSON")
                        
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON: {e}")
        else:
            self.logger.warning("Could not find the Hypernova script tag")

    def parse_category(self, response):
        # Extract product links from category page
        product_links = response.css('a[data-testid="itemLink"]::attr(href)').getall()
        
        self.logger.info(f"Found {len(product_links)} products in {response.meta.get('category_name', 'category')}")
        
        for link in product_links[:10]:  # LIMIT: 10 per category for testing
            product_url = response.urljoin(link)
            if product_url not in self.seen_urls:
                self.seen_urls.add(product_url)
                yield scrapy.Request(
                    url=product_url,
                    callback=self.parse_product,
                    meta={'category_name': response.meta['category_name']}
                )

    def parse_product(self, response):
        # Extract product title
        product_name = response.css('h1::text').get()
        if not product_name:
            product_name = response.xpath('//h1/text()').get()
        product_name = product_name.strip() if product_name else "N/A"
        
        # Extract image link
        image_link = response.css('img#GalleryImage::attr(src)').get()
        
        # Extract overview from highlights section
        overview_bullets = response.css('div[data-testid="highlights-meta-side-section"] ul li span::text').getall()
        overview = " | ".join([bullet.strip() for bullet in overview_bullets if bullet.strip()])
        
        # Extract manufacturer number
        mfr = response.css('span[data-testid="product-detail-heading-vendor-number"] span.uppercase::text').get()
        
        # Helper function to extract specifications
        def get_spec(spec_name):
            xpath_query = f'//dt[contains(., "{spec_name}")]/following-sibling::dd[1]//text()'
            texts = response.xpath(xpath_query).getall()
            cleaned_texts = [t.strip() for t in texts if t.strip() and t.strip() != '\xa0']
            return ", ".join(cleaned_texts) if cleaned_texts else "N/A"
        
        product = {
            'name': product_name,
            'category_name': response.meta.get('category_name', ''),
            'product_url': response.url,
            'image_link': response.urljoin(image_link) if image_link else "N/A",
            'manufacturer': mfr.strip() if mfr else "N/A",
            'overview': overview if overview else "N/A",
            'length': get_spec('Length'),
            'width': get_spec('Width'),
            'height': get_spec('Height'),
            'diameter': get_spec('Diameter'),
            'volume_capacity': get_spec('Capacity'),
            'material': get_spec('Material'),
            'color': get_spec('Color'),
            'shape': get_spec('Shape'),
            'pattern': get_spec('Pattern'),
            'features': get_spec('Features'),
            'edge_style': get_spec('Edge Style'),
            'country_of_origin': get_spec('Country of Origin'),
        }
        
        self.product_data.append(product)
        self.logger.info(f"✓ {product_name[:50]}")
        yield product

    def closed(self, reason):
        self.save_to_csv(self.csv_filename)
        self.logger.info(f"Total products scraped: {len(self.product_data)}")

    def save_to_csv(self, filename):
        if not self.product_data:
            self.logger.info("No product data to save")
            return
        
        fieldnames = [
            'name', 'category_name', 'manufacturer', 'image_link', 'overview',
            'length', 'width', 'height', 'diameter', 'volume_capacity',
            'material', 'color', 'shape', 'pattern', 'features', 'edge_style',
            'country_of_origin', 'product_url'
        ]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(self.product_data)
            self.logger.info(f"✓ Saved {len(self.product_data)} products to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
