import hashlib
from bs4 import BeautifulSoup
from scrapy import Request, cmdline
import scrapy
from pymongo import MongoClient

'''
近现代人物名录网站更新后的爬虫，网站标记总数据47197
'''


class Pcv2Spider(scrapy.Spider):
    name = "pcv2"
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
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'activexime_enable=false; WMONID=gsztIr8bOsI; PCID=17363157138466054625677; JSESSIONID=G8X59NiNNuI7m4z3L14kASLtpWLmiygAqYyCJ_Vr.node10; RC_RESOLUTION=1920*1080; RC_COLOR=24',
        'Origin': 'https://db.history.go.kr',
        'Pragma': 'no-cache',
        'Referer': 'https://db.history.go.kr/contemp/search/searchResultList.do',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }

    # client = MongoClient(os.environ.get('MONGO_URI'))
    client = MongoClient('localhost', 27017)
    db = client['korea_analysis']
    collection = db['persopn_category_v2_02']
    reflect_map = {
        '이름': 'name',
        '민족구분': 'ethnic_distinction',
        '출신지': 'born_place',
        '현주소': 'live_place',
        '현직업': 'occupation',
        '학력': 'degree',
        '경력및활동': 'experiences_and_activities',
        '참고문헌': 'reference',
    }

    def start_requests(self):
        payload = 'pageIndex=1&pageUnit=100000&pageSize=1&orderColumn=levelId&orderDir=ASC&synonym=off&chinessChar=on&wordImages=&totalWord=&titleWord=&titleConjunction=AND&contentsWord=&contentsConjunction=AND&creatorWord=&creatorConjunction=AND&startDate=&endDate=&itemOnlyYn=N&searchItemIds=&searchItemId=im&searchLevel1Id=&searchTypes=o&searchSujectClass1=&itemSearchCount=47197'
        url = "https://db.history.go.kr/contemp/search/searchResultList.do"
        yield Request(method='POST', url=url, body=payload, callback=self.parse_level1_tab_links,
                      headers=self.headers)

    def parse_level1_tab_links(self, response):
        def fnGoItemLevel(searchItemId, path, position):
            item_info = {
                'searchItemId': searchItemId,
                'path': path,
                'position': position
            }
            return item_info

        items = response.xpath('//div[@class="list-table"]//div[@class="list-item"]')
        for item in items:
            onclick = item.xpath('.//a/@onclick').get()
            onclick = onclick.split(';')[0]
            item_info = eval(onclick)
            url = f'https://db.history.go.kr/contemp/{item_info["searchItemId"]}/detail.do'
            payload = f'position={item_info["position"]}&pageIndex=1&pageUnit=100&pageSize=1&orderColumn=levelId&orderDir=ASC&synonym=off&chinessChar=on&wordImages=&totalWord=&titleWord=&titleConjunction=AND&contentsWord=&contentsConjunction=AND&creatorWord=&creatorConjunction=AND&startDate=&endDate=&itemOnlyYn=N&searchItemIds=&searchItemId={item_info["searchItemId"]}&searchLevel1Id=&searchTypes=o&searchSujectClass1=&itemSearchCount=47197'
            lis = item.xpath('.//div[@class="other"]//li')
            brief = {}
            for i in lis:
                get = i.xpath('./text()').get()
                split = get.split('|')
                brief[self.clean(split[0])] = self.clean(split[1])
            yield Request(method='POST', url=url, body=payload, callback=self.parse_details, headers=self.headers,
                          meta={'brief': brief, 'item_info': item_info},
                          dont_filter=True)
            # break

    def parse_details(self, response):
        brief = response.meta['brief']
        item_info = response.meta['item_info']
        id_searchItemId = item_info['searchItemId']
        position = item_info['position']
        item_nodes = response.xpath('//section[@class="section-meta"]//div[@class="item"]')
        item = {
            'brief': brief,
            'item_info': item_info,
            'unique_id': hashlib.md5((id_searchItemId + position).encode()).hexdigest()
        }

        for item_node in item_nodes:
            key = item_node.xpath('./div[@class="tit"]/text()').get()
            soup = BeautifulSoup(item_node.xpath('./div[@class="cont"]').get(), 'lxml')
            value = soup.get_text()
            if key == '이름':
                item['person_name'] = self.clean(value)
            else:
                if key in self.reflect_map:
                    item[self.reflect_map[key]] = value
                else:
                    item[key] = value

        self.collection.insert_one(item)

    def clean(self, text):
        if text:
            return text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()
        else:
            return ''


cmdline.execute('scrapy crawl pcv2'.split())
