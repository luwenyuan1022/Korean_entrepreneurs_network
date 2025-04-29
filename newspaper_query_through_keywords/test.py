import requests
import json

url = "https://nl.go.kr/newspaper/search_newspaper.do"

payload = json.dumps({
  "facetedType": [],
  "facetedData": [],
  "search_keyword": " 东洋拓殖",
  "page_size": 10,
  "page_no": 0
})
headers = {
  'Accept': 'application/json, text/javascript, */*; q=0.01',
  'Accept-Language': 'zh-CN,zh;q=0.9',
  'Cache-Control': 'no-cache',
  'Connection': 'keep-alive',
  'Content-Type': 'application/json',
  # 'Cookie': 'JSESSIONID=658326F64C8220E2FDF14783195A03B9; PCID=753b0db9-cb2a-8ce6-fd1a-026e56d70360-1737023862165',
  'Origin': 'https://nl.go.kr',
  'Pragma': 'no-cache',
  # 'Referer': 'https://nl.go.kr/newspaper/keyword_search.do?search_keyword=+%E4%B8%9C%E6%B4%8B%E6%8B%93%E6%AE%96',
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'same-origin',
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
  'X-Requested-With': 'XMLHttpRequest',
  'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"macOS"'
}

response = requests.request("POST", url, headers=headers, data=payload)
response.json()
print(response.text)
