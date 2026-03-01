import scrapy
from scrapy import Request
import re
import json


class WilliamsfoodequipmentSpider(scrapy.Spider):
    name = "williamsfoodequipment"
    allowed_domains = ["williamsfoodequipment.com"]
    start_urls = ["https://williamsfoodequipment.com/search.php?search_query=Steelite+"]
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
    }

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url,
                callback=self.parse,
                meta={'playwright': True}
            )

    def parse(self, response):
        product_links = response.css('li.klevuProduct a.klevuProductClick::attr(href)').getall()
        self.logger.info(f"Found {len(product_links)} product links on {response.url}")
        
        # Remove duplicates and follow each product link
        for link in set(product_links):
            if link:
                self.logger.info(f"Following product link: {link}")
                yield Request(
                    url=response.urljoin(link),
                    callback=self.parse_product,
                    dont_filter=False,
                    meta={'playwright': True}
                )
        
        # Handle pagination if needed
        next_page = response.css('a.pagination-next::attr(href)').get()
        if next_page:
            self.logger.info(f"Following pagination: {next_page}")
            yield Request(
                url=response.urljoin(next_page),
                callback=self.parse,
                meta={'playwright': True}
            )

    def parse_product(self, response):
        self.logger.info(f"Parsing product: {response.url}")
        
        def extract_spec(spec_name):
            xpath = f"//td[contains(text(), '{spec_name}')]/following-sibling::td/text()"
            value = response.xpath(xpath).get()
            return value.strip() if value else None

        # Extract product name
        product_name = response.css('h1.productView-title::text').get()
        if not product_name:
            product_name = response.xpath('//meta[@property="og:title"]/@content').get()
        if not product_name:
            product_name = response.css('h1::text').get()
        
        self.logger.info(f"Product name: {product_name}")
        
        # Extract main product image
        image_url = response.css('img.productView-image--default::attr(src)').get()
        if not image_url:
            image_url = response.xpath('//meta[@property="og:image"]/@content').get()
        if not image_url:
            image_url = response.css('img[class*="product"]::attr(src)').get()
        
        # Extract price
        sale_price = response.css('span.productView-reviewPrice--salePrice::text').get()
        regular_price = response.css('span.productView-reviewPrice--original::text').get()
        
        if not sale_price:
            sale_price = response.xpath('//span[contains(@class, "sale")]/text()').get()
        if not regular_price:
            regular_price = response.xpath('//span[contains(@class, "original") or contains(@class, "regular")]/text()').get()
        
        # Extract product description/overview
        overview = response.css('div.productView-description ::text').getall()
        if not overview:
            overview = response.css('div[class*="description"] ::text').getall()
        overview = ' '.join([text.strip() for text in overview if text.strip()])
        
        # Extract all product specifications from the specifications table
        specs = {}
        spec_rows = response.css('table.table.table-striped.table-bordered tbody tr')
        
        for row in spec_rows:
            spec_title = row.css('td.productView-specifications_title::text').get()
            spec_value = row.css('td.productView-specifications_value::text').get()
            
            if spec_title and spec_value:
                specs[spec_title.strip()] = spec_value.strip()
        
        # Extract prioritized specifications
        brand = specs.get('Brand')
        series = specs.get('Series')
        product_type = specs.get('Type')
        capacity = specs.get('Capacity')
        color = specs.get('Color')
        material = specs.get('Material')
        size = specs.get('Size')
        case_pack_size = specs.get('Case Pack Size')
        warranty = specs.get('Warranty')
        
        # Extract dimension and volume specifications
        length = specs.get('Length')
        width = specs.get('Width')
        height = specs.get('Height')
        volume = specs.get('Volume')
        diameter = specs.get('Diameter')
        pattern = specs.get('Pattern')
        
        # Extract identifiers and codes
        sku = response.xpath('//span[contains(text(), "SKU:")]/following-sibling::span/text()').get()
        if not sku:
            sku = response.css('span.product_sku::text').get()
        
        # Extract MFR (manufacturer code) from BCData JavaScript object
        mfr = specs.get('MFR') or specs.get('Manufacturer Code') or specs.get('Mfr')
        if not mfr:
            # Extract from BCData JSON in script tag
            bcdata_script = response.xpath('//script[contains(text(), "var BCData")]/text()').get()
            if bcdata_script:
                # Extract the JSON part from: var BCData = {...};
                match = re.search(r'var BCData = ({.*?});', bcdata_script, re.DOTALL)
                if match:
                    try:
                        bcdata = json.loads(match.group(1))
                        mfr = bcdata.get('product_attributes', {}).get('mpn')
                    except json.JSONDecodeError:
                        self.logger.warning(f"Failed to parse BCData JSON on {response.url}")
        
        # Extract EAN/Barcode codes
        ean_code = specs.get('EAN Code') or specs.get('EAN') or specs.get('EAN13')
        barcode = specs.get('Barcode') or specs.get('UPC') or specs.get('Barcode/EAN')
        
        # Extract stock availability
        availability = response.xpath('//meta[@property="og:availability"]/@content').get()
        in_stock = availability == 'instock' if availability else None
        
        # Return prioritized fields
        yield {
            'product_name': product_name.strip() if product_name else None,
            'url': response.url,
            'image_link': image_url,
            'overview': overview if overview else None,
            'length': length,
            'width': width,
            'height': height,
            'volume': volume,
            'diameter': diameter,
            'color': color,
            'material': material,
            'ean_code': ean_code,
            'pattern': pattern,
            'barcode': barcode,
            'mfr': mfr,
            'sku': sku,
            'brand': brand,
            'series': series,
            'type': product_type,
            'capacity': capacity,
            'case_pack_size': case_pack_size,
            'warranty': warranty,
            'sale_price': sale_price.strip() if sale_price else None,
            'regular_price': regular_price.strip() if regular_price else None,
            'in_stock': in_stock,
        }
