import re
import scrapy


class KitchenrestockSpider(scrapy.Spider):
    name = "kitchenrestock"
    allowed_domains = ["kitchenrestock.com"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 25,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 15,
        "AUTOTHROTTLE_MAX_DELAY": 180,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 0.1,
        "RETRY_TIMES": 8,
        "RETRY_HTTP_CODES": [429, 500, 502, 503, 504, 522, 524, 408],
        "HTTPERROR_ALLOWED_CODES": [429],
    }

    def __init__(self, start_page=1, end_page=861, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_page = int(start_page)
        self.end_page = int(end_page)
        self.seen = set()

    async def start(self):
        yield scrapy.Request(
            self._search_url(self.start_page),
            callback=self.parse_search,
            cb_kwargs={"page": self.start_page},
            dont_filter=True,
        )

    def _search_url(self, page: int) -> str:
        return f"https://kitchenrestock.com/search?options%5Bprefix%5D=last&page={page}&q=Steelite+"

    def parse_search(self, response, page: int):
        if response.status == 429:
            retry_after = int(response.headers.get("Retry-After", b"60").decode("utf-8", "ignore") or 60)
            self.logger.warning("429 on page=%s, retry-after=%ss", page, retry_after)
            yield response.request.replace(dont_filter=True, priority=response.request.priority - 10)
            return

        links = response.css("li.js-pagination-result a.js-prod-link::attr(href)").getall()
        if not links:
            links = response.css("product-card a.js-prod-link::attr(href)").getall()

        for href in links:
            url = response.urljoin(href.split("?")[0])
            if url in self.seen:
                continue
            self.seen.add(url)
            yield scrapy.Request(url, callback=self.parse_product)

        if page < self.end_page and links:
            next_page = page + 1
            yield scrapy.Request(
                self._search_url(next_page),
                callback=self.parse_search,
                cb_kwargs={"page": next_page},
                dont_filter=True,
            )
