import scrapy
import json

class WebstaurantstoreSpider(scrapy.Spider):
    name = "webstaurantstore"
    allowed_domains = ["www.webstaurantstore.com"]
    start_urls = ["https://www.webstaurantstore.com/vendor/steelite-international.html"]

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    }

    def parse(self, response):
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
                
                seen_urls = set()
                for category in extract_categories(data):
                    if category['url'] not in seen_urls:
                        seen_urls.add(category['url'])
                        
                        yield scrapy.Request(
                            url=category['url'],
                            callback=self.parse_category,
                            meta={'category_name': category['title']}
                        )
                        
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON: {e}")
        else:
            self.logger.warning("Could not find the Hypernova script tag.")

    def parse_category(self, response):
        category_name = response.meta['category_name']
        product_links = response.css('a[data-testid="itemLink"]::attr(href)').getall()
        
        for link in product_links:
            yield scrapy.Request(
                url=response.urljoin(link),
                callback=self.parse_product,
                meta={'category_name': category_name} 
            )

    def parse_product(self, response):
        image_link = response.css('img#GalleryImage::attr(src)').get()
        
        overview_bullets = response.css('div[data-testid="highlights-meta-side-section"] ul li span::text').getall()
        overview = " | ".join([bullet.strip() for bullet in overview_bullets if bullet.strip()])
        
        mfr = response.css('span[data-testid="product-detail-heading-vendor-number"] span.uppercase::text').get()

        def get_spec(spec_name):
            xpath_query = f'//dt[contains(., "{spec_name}")]/following-sibling::dd[1]//text()'
            texts = response.xpath(xpath_query).getall()
            cleaned_texts = [t.strip() for t in texts if t.strip() and t.strip() != '\xa0']
            return ", ".join(cleaned_texts)

        yield {
            'category_name': response.meta['category_name'],
            'product_url': response.url,
            'image_link': response.urljoin(image_link) if image_link else None,
            'mfr': mfr.strip() if mfr else None,
            'overview': overview,
            'length': get_spec('Length'),
            'width': get_spec('Width'),
            'height': get_spec('Height'),
            'capacity': get_spec('Capacity'),
            'diameter': get_spec('Diameter'),
            'features': get_spec('Features'),
            'edge_style': get_spec('Edge Style'),
            'color': get_spec('Color'),
            'shape': get_spec('Shape'),
            'material': get_spec('Material')
        }