import hashlib
import os
import re

from scrapy import Request, cmdline
import scrapy
from pymongo import MongoClient
from scrapy.selector.unified import SelectorList


class OfficialsSpiderSpider(scrapy.Spider):
    name = "officials_spider"
    custom_settings = {
        # "DOWNLOAD_DELAY": 0.1,
        "DOWNLOAD_TIMEOUT": 200,
        "IGNORE_ITEM_LOG": True,
        "LOG_LEVEL": "INFO",
        "ROBOTSTXT_OBEY": False,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 30,  # 重试次数+
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
    client = MongoClient(os.environ.get('MONGO_URI'))
    # client = MongoClient('localhost', 27017)
    db = client['korea_analysis']
    collection = db['korea_officials_category']
    total_count = 0
    leve1_name_list = ['대한제국', '조선총독부', '대한민국', '대만총독부']
    level1_name_and_years_map = {}
    page_size = 200000
    'https://db.history.go.kr/contemp/jw/level.do?organCode=1943-11-357&lang=ch&pageIndex=1&orderColumn=level_id&recordCountPerPage=200'

    def start_requests(self):
        url = 'https://db.history.go.kr/contemp/jw/level.do'
        yield Request(url, callback=self.get_years, headers=self.headers)

    def extract_onclick_text(self, text):
        return re.findall(r"\'(.+?)\'", text)

    def get_cleaned_field_name(self, text):
        if text:
            return text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').replace(' ', '').replace('-',
                                                                                                          '').strip()
        else:
            return ''

    # def get_deepest_level_code(self, text):
    #     return re.findall(r"\'(.+?)\'", text)

    def get_years(self, response):
        search_sections = response.xpath('//div[@class="search-section"]')
        for i in search_sections:
            items = i.xpath('./div[@class="item" and not(@data-code)]')
            for j in items:
                lis = j.xpath('.//li')
                for li in lis:
                    onclick_text = li.xpath('./@onclick').get()
                    res_list = self.extract_onclick_text(onclick_text)
                    leve1_name = res_list[0]
                    year = res_list[1]
                    if leve1_name not in self.level1_name_and_years_map:
                        self.level1_name_and_years_map[leve1_name] = [year]
                    else:
                        self.level1_name_and_years_map[leve1_name].append(year)
        for k, v in self.level1_name_and_years_map.items():
            print(f'{k} 共有{len(v)}个年份，{v}')
            for i in v:
                url = f'https://db.history.go.kr/contemp/jw/level.do?types={k}&year={i}'
                yield Request(url, callback=self.get_level_1, headers=self.headers,
                              meta={'tab': k, 'year': i, 'category': f'{k}:::{i}'})

    def get_level_1(self, response):
        meta = response.meta
        year = meta['year']
        category = meta['category']
        lis = response.xpath(f'//div[@data-code="{year}"]//li')
        for i in lis:
            data_id = i.xpath('./@data-id').get()
            level1_name = i.xpath('./a/text()').get()
            url = f'https://db.history.go.kr/contemp/jw/level.do?organCode={data_id}&pageIndex=1&orderColumn=level_id&recordCountPerPage={self.page_size}'
            yield Request(url, callback=self.get_level_n, headers=self.headers,
                          meta={'category': f'{category}:::{level1_name}', 'data_id': data_id})

    def get_next_level_list(self, response, data_id) -> SelectorList:
        return response.xpath(f'//div[@data-code="{data_id}"]//li')

    def get_level_n(self, response):
        meta = response.meta
        category = meta['category']
        data_id = meta['data_id']
        self.insert_current_level_items(response, category)
        lis = self.get_next_level_list(response, data_id)
        if lis:
            for i in lis:
                new_data_id = i.xpath('./@data-id').get()
                level_n_name = i.xpath('./a/text()').get()
                url = f'https://db.history.go.kr/contemp/jw/level.do?organCode={new_data_id}&pageIndex=1&orderColumn=level_id&recordCountPerPage={self.page_size}'
                yield Request(url, callback=self.get_level_n, headers=self.headers,
                              meta={'category': f'{category}:::{level_n_name}', 'data_id': new_data_id})

    def insert_current_level_items(self, response, category):
        table_items = response.xpath(f'//div[@class="table-cont"]//div[@class="table-item"]')
        if table_items:
            for i in table_items:
                item = {}
                person_name = i.xpath('./div[@class="subject"]/text()').get()
                if not person_name:
                    print(response.url)
                    continue
                fields_divs = i.xpath('./div[@class="info"]//div')
                for j in fields_divs:
                    field_name = self.get_cleaned_field_name(j.xpath('./span/text()').get())
                    field_value = self.clean(j.xpath('./text()').get())
                    if field_name and field_value:
                        item[field_name] = field_value
                item['person_name'] = person_name
                item['category'] = category
                item['url'] = response.url
                item['unique_id'] = hashlib.md5(f'{category}_{person_name}'.encode()).hexdigest()
                self.collection.insert_one(item)

    def clean(self, text):
        if text:
            return text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()
        else:
            return ''


cmdline.execute('scrapy crawl officials_spider'.split())
