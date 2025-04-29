import base64

import requests
from pymongo import MongoClient

url = "https://viewer.nl.go.kr/nlmivs/view_image.jsp?cno=CNTS-00093813268&vol=0&page=1&twoThreeYn=N"

payload = {}
headers = {
  'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
  'Accept-Language': 'zh-CN,zh;q=0.9',
  'Cache-Control': 'no-cache',
  'Connection': 'keep-alive',
  'Cookie': 'PCID=753b0db9-cb2a-8ce6-fd1a-026e56d70360-1737023862165; WMONID=-sQRyZuJtHI; JSESSIONID="fzeGbK5UrE7dK7oBx3AG6-Q8JAfUNmmuQ-1uwU_Y.VWWAS1:tv-1"',
  'Pragma': 'no-cache',
  'Referer': 'https://viewer.nl.go.kr/main.wviewer',
  'Sec-Fetch-Dest': 'image',
  'Sec-Fetch-Mode': 'no-cors',
  'Sec-Fetch-Site': 'same-origin',
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
  'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"macOS"'
}
client = MongoClient('localhost', 27017)
db = client['crawlers']
collection = db['pics']
response = requests.request("GET", url, headers=headers, data=payload)
base64_image = base64.b64encode(response.content)
collection.insert_one({'content': base64_image})
