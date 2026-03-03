#!/usr/bin/env python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "sanneng"))

from scrapy.crawler import CrawlerProcess
from sanneng.spiders.chakawal import ChakawalSpider

process = CrawlerProcess({
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0',
    'ROBOTSTXT_OBEY': False,
    'DOWNLOAD_DELAY': 2,
    'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
})

process.crawl(ChakawalSpider)
process.start()
