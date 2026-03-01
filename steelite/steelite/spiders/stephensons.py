import scrapy

class StephensonsSpider(scrapy.Spider):
    name = "stephensons"
    allowed_domains = ["www.stephensons.com"]
    start_urls = ["https://www.stephensons.com/catering-crockery/steelite-crockery"]

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
    }

    def parse(self, response):
        categories = response.css('.category-a-wrapper a.title::attr(href)').getall()
        
        for category_url in categories:
            yield scrapy.Request(
                url=category_url,
                callback=self.parse_subcategory
            )

    def parse_subcategory(self, response):
        subcategories = response.css('.category-a-wrapper a.title::attr(href)').getall()
        
        for subcategory_url in subcategories:
            yield scrapy.Request(
                url=subcategory_url,
                callback=self.parse_products
            )

    def parse_products(self, response):
        product_links = response.css('li.product-item a.product-item-photo::attr(href)').getall()
        
        for product_url in product_links:
            yield scrapy.Request(
                url=product_url,
                callback=self.parse_product_details
            )

        next_page = response.css('.pages-item-next a::attr(href)').get()
        if next_page:
            yield scrapy.Request(url=next_page, callback=self.parse_products)

    def parse_product_details(self, response):
        image_link = response.css('meta[property="og:image"]::attr(content)').get()
        
        overview_texts = response.xpath('//div[contains(@class, "product attribute description")]//div[@class="value"]//text()[not(ancestor::style) and not(ancestor::script)]').getall()
        overview = " | ".join([text.strip() for text in overview_texts if text.strip()])
        
        mfr = response.css('div.product.attribute.sku div.value::text').get()
        if not mfr:
            # Fallback just in case it's hidden in the itemprop schema instead
            mfr = response.css('[itemprop="sku"]::text, [itemprop="mpn"]::text').get()
        
        def get_spec(spec_name):
            lower_spec = spec_name.lower()
            
            # Looks in ANY table for a header containing the spec name, and grabs the cell next to it
            xpath_query = f'//table//th[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{lower_spec}")]/following-sibling::td//text()'
            texts = response.xpath(xpath_query).getall()
            
            # Clean up the output
            cleaned_texts = [t.strip() for t in texts if t.strip() and t.strip() != '\xa0']
            return ", ".join(cleaned_texts)

        yield {
            'product_url': response.url,
            'image_link': image_link,
            'mfr': mfr.strip() if mfr else None, # MFR Added Here
            'overview': overview,
            'length': get_spec('Length'),
            'width': get_spec('Width'),
            'height': get_spec('Height'),
            'volume': get_spec('Volume'),
            'diameter': get_spec('Diameter'),
            'color': get_spec('Color'),
            'material': get_spec('Material'),
            'ean_code': get_spec('EAN'), # Shortened to EAN to catch both 'EAN' and 'EAN Code'
            'pattern': get_spec('Pattern'),
            'barcode': get_spec('Barcode')
        }