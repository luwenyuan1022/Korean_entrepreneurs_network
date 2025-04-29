import hashlib
import os
import re

from scrapy import Request, cmdline
import scrapy
from pymongo import MongoClient


class PersopnCategorySpiderSpider(scrapy.Spider):
    name = "persopn_category_spider"
    custom_settings = {
        # "DOWNLOAD_DELAY": 0.1,
        "DOWNLOAD_TIMEOUT": 200,
        "IGNORE_ITEM_LOG": True,
        "LOG_LEVEL": "INFO",
        "ROBOTSTXT_OBEY": False,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 30,  # 重试次数
        'REDIRECT_MAX_TIMES': 15,
        "RETRY_HTTP_CODES": [401, 402, 403, 407, 429, 500, 502, 503],
        'COOKIES_ENABLE': False
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }
    domain = 'https://db.history.go.kr'
    # client = MongoClient(os.environ.get('MONGO_URI'))
    client = MongoClient('localhost', 27017)
    db = client['crawlers']
    collection = db['persopn_category']

    def start_requests(self):
        url = f"https://db.history.go.kr/contemp/im/level.do;jsessionid=oli1hyBos9YWjMqUblX7GQyMO9mmNnBd8mtdr02_.node10?itemId=&levelId=&pageIndex=1&indexOrder=&searchWrd=&recordCountPerPage=100000&orderColumn=level_id"
        yield Request(url, callback=self.parse_level1_tab_links, headers=self.headers)

    def parse_level1_tab_links(self, response):
        def contempViewPage(params, path):
            res = {
                'params': params,
                'path': path
            }
            return res

        a_s = response.xpath('//div[@class="table-cont"]//a')
        for a in a_s:
            onclick = a.xpath('./@onclick').get()
            url_info = eval(onclick)
            url = f'https://db.history.go.kr{url_info["path"]}?pageIndex=1&recordCountPerPage=100&orderColumn=level_id&levelId={url_info["params"]}'
            yield Request(url, callback=self.parse_details, headers=self.headers)
            # break

    def parse_details(self, response):
        item_nodes = response.xpath('//section[@class="section-meta"]//div[@class="item"]')
        item = {
            'url': response.url,
            'unique_id': hashlib.md5(response.url.encode()).hexdigest()
        }
        for item_node in item_nodes:
            key = item_node.xpath('./div[@class="tit"]/text()').get()
            value = item_node.xpath('./div[@class="cont"]/text()').get()
            item[key] = self.clean(value) if key == '이름' else value
        self.collection.insert_one(item)

    def clean(self, text):
        if text:
            return text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()
        else:
            return ''


cmdline.execute('scrapy crawl persopn_category_spider'.split())
