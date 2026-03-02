import scrapy


class GaenSpider(scrapy.Spider):
    name = "gaen"
    allowed_domains = [""]
    start_urls = [""]

    def parse(self, response):
        pass
