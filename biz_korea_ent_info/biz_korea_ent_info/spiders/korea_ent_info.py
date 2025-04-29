import hashlib
import os
import re

from scrapy import Request, cmdline
import scrapy
from pymongo import MongoClient


class KoreaEntInfoSpider(scrapy.Spider):
    name = "korea_ent_info"
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
    level1_name_map = {
        '001': '해방 전 회사자료',
        '002': '해방 전 조합자료',
        '003': '해방 이후 회사자료'
    }
    domain = 'https://db.history.go.kr'
    client = MongoClient(os.environ.get('MONGO_URI'))
    # client = MongoClient('localhost', 27017)
    db = client['crawlers']
    collection = db['korea_ent_info']
    total_count = 0

    def start_requests(self):
        url = 'https://db.history.go.kr/contemp/hs/level.do?level1=002&level2=1929&part1=hs_002_1929&subjectClass=%EA%B8%88%EC%9C%B5%EC%A1%B0%ED%95%A9&itemId=hs#none'
        yield Request(url, callback=self.parse_level1_tab_links, headers=self.headers)

    def parse_level1_tab_links(self, response):
        def getData(modal_no, year, submodal_name, hs='hs'):
            res = {
                'modal_no': modal_no,
                'year': year,
                'submodal_name': submodal_name,
                'hs': hs
            }
            return res

        main_tabs = response.xpath('//div[@class="search-cont"]')
        for j in main_tabs:
            items = j.xpath('.//div[@class="item" and @data-depth3]')
            for k in items:
                lis = k.xpath('.//li[@onclick]')
                print(len(lis))
                for i in lis:
                    onclick_attr = i.xpath('./@onclick').get()
                    num_with_name = i.xpath('./a/text()').get()
                    print(num_with_name)
                    self.total_count += int(re.findall('\d+', num_with_name)[0])
                    url_info = eval(onclick_attr)
                    # if int(url_info['year']) > 1949: #这句可以用于过滤年份抓取
                    params_chain = f'itemId={url_info["hs"]}&pageIndex=1&level1={url_info["modal_no"]}&level2={url_info["year"]}&part1={url_info["hs"]}_{url_info["modal_no"]}_{url_info["year"]}&subjectClass={url_info["submodal_name"]}'
                    url = f'{self.domain}/contemp/hs/level.do?{params_chain}&recordCountPerPage=100000&orderColumn=level_id&type=&searchWrd='
                    url_info['params_chain'] = params_chain
                    yield Request(url, callback=self.parse_links, headers=self.headers, meta=url_info)
        print(self.total_count)

    def parse_links(self, response):
        def contempViewPage(tag, path):
            res = {
                'tag': tag,
                'path': path
            }
            return res

        meta = response.meta.copy()
        subjects = response.xpath('//*[@id="table"]//div[@class="subject"]')
        print(len(subjects))
        for subject in subjects:
            onclick_attr = subject.xpath('./a[@onclick]/@onclick').get()
            url_info = eval(onclick_attr)
            ent_name = subject.xpath('./a/text()').get()
            url = f'{self.domain}/contemp/hs/detail.do?{meta["params_chain"]}&recordCountPerPage=100000&orderColumn=level_id&levelId={url_info["tag"]}'
            meta['ent_name'] = self.clean(ent_name)
            yield Request(url, callback=self.parse_details, headers=self.headers, meta=meta)

    def parse_details(self, response):
        meta = response.meta
        item_nodes = response.xpath('//section[@class="section-meta"]//div[@class="item"]')
        item = {
            'ent_name': meta['ent_name'],
            'category': f'{self.level1_name_map[meta["modal_no"]]}>{meta["year"]}>{meta["submodal_name"]}',
            'url': response.url,
            'unique_id': hashlib.md5(response.url.encode()).hexdigest(),
            'year': meta['year']
        }
        for item_node in item_nodes:
            key = item_node.xpath('./div[@class="tit"]/text()').get()
            value = item_node.xpath('./div[@class="cont"]/text()').get()
            item[key] = self.clean(value)
        self.collection.insert_one(item)

    def clean(self, text):
        if text:
            return text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()
        else:
            return ''


cmdline.execute('scrapy crawl korea_ent_info'.split())
