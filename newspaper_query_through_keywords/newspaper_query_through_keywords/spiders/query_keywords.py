import hashlib
import json
import os
import re

from scrapy import Request, cmdline
import scrapy
from pymongo import MongoClient


class QueryKeywordsSpider(scrapy.Spider):
    name = "query_keywords"
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
    # client = MongoClient(os.environ.get('MONGO_URI'))
    client = MongoClient('localhost', 27017)
    db = client['crawlers']
    collection = db['newspaper_query_through_keywords']
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://nl.go.kr',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }
    keywords_dict = {}
    with open('./final_name_json.txt', 'r', encoding='utf') as f:
        for i in f.readlines():
            keywords_dict.update(json.loads(i.replace('\n', '')))

    max_page_size = 0

    def start_requests(self):
        url = "https://nl.go.kr/newspaper/search_newspaper.do"
        for k, v in self.keywords_dict.items():
            payload = json.dumps({
                "facetedType": [],
                "facetedData": [],
                "search_keyword": k,
                "page_size": 1000000,
                "page_no": 0
            })
            yield Request(method='POST', url=url, callback=self.parse, headers=self.headers, body=payload,
                          dont_filter=True, meta={'extra': {'source_keywords': str(v), 'keyword': k}})
            # break

    def parse(self, response):
        meta = response.meta
        extra = meta['extra']
        keyword = extra['keyword']
        hits_list = response.json()['hits']
        length_curr = len(hits_list)
        if length_curr > self.max_page_size:
            self.max_page_size = length_curr
            print('Max page size now is {}'.format(self.max_page_size))
        for i in hits_list:
            for k, v in i.items():
                if isinstance(v, list):
                    i[k] = ':::'.join(v)
            i.update(extra)
            self.collection.insert_one(i)
        # del self.keywords_dict[keyword]


cmdline.execute('scrapy crawl query_keywords'.split())
