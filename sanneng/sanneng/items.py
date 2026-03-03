# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SannengItem(scrapy.Item):
    # Product identification
    name = scrapy.Field()
    sku = scrapy.Field()  # Manufacturer/Model number (MFR)
    
    # Product details
    image_link = scrapy.Field()
    overview = scrapy.Field()
    
    # Dimensions
    length = scrapy.Field()
    width = scrapy.Field()
    height = scrapy.Field()
    diameter = scrapy.Field()
    volume = scrapy.Field()
    
    # Other attributes
    color = scrapy.Field()
    material = scrapy.Field()
    pattern = scrapy.Field()
    
    # Codes
    ean_code = scrapy.Field()
    barcode = scrapy.Field()
    upc = scrapy.Field()
    
    # URLs
    product_url = scrapy.Field()
    
    # Source website
    source = scrapy.Field()
