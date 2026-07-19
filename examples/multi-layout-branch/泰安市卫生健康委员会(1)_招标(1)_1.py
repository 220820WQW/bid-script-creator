# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re

# region static methods
def auto_request(url, params=None, data=None, json=None, proxy_safety=None, **kwargs):
    proxy_safety = urlparse(url).scheme if proxy_safety is None else proxy_safety

    if data is not None or json is not None:
        resp = request.post(url, params=params, data=data, json=json, proxy_safety=proxy_safety, **kwargs)
    else:
        resp = request.get(url, params=params, proxy_safety=proxy_safety, **kwargs)

    resp.encoding = resp.apparent_encoding
    return resp


def is_same_origin_url(url_a: str, url_b: str):
    suffix = {".pdf", ".doc", ".docx", ".xls", ".xlsx"}

    def _is_attachment(url: str):
        path = urlparse(url).path.lower()
        return path.endswith(tuple(suffix))

    def _get_domain(url: str):
        hostname = urlparse(url).hostname or ""
        hostname = hostname.lower()
        if hostname.startswith('www.'):
            hostname = hostname[4:]
        return hostname

    if _is_attachment(url_a) or _is_attachment(url_b):
        return False

    domain_a = _get_domain(url_a)
    domain_b = _get_domain(url_b)
    return domain_a == domain_b


# endregion


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}
COOKIES = {}


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 业务公告
            {
                "url": "http://wjw.taian.gov.cn/col/col45777/index.html",
                "page_number": 1,
                "t": 1
            },
            # 公告栏
            {
                "url": "http://wjw.taian.gov.cn/col/col45779/index.html",
                "page_number": 1,
                "t": 1
            },
            # 政策法规
            {
                "url": "http://wjw.taian.gov.cn/col/col45778/index.html",
                "page_number": 1,
                "t": 1
            },
            # 专项规划
            {
                "url": "http://wjw.taian.gov.cn/module/xxgk/search.jsp",
                "page_number": 1,
                "t": 2,
                "data": {
                    "divid": "div4",
                    "infotypeId": "TA3202",
                    "jdid": "344",
                    "area": "",
                    "sortfield": "createdatetime:0",
                    "standardXxgk": "1",
                }
            },
            # 抽查结果
            {
                "url": "http://wjw.taian.gov.cn/module/xxgk/search.jsp",
                "page_number": 1,
                "t": 2,
                "data": {
                    "divid": "div4",
                    "infotypeId": "TA41030402",
                    "jdid": "344",
                    "area": "",
                    "sortfield": "createdatetime:0",
                    "standardXxgk": "1",
                }
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                item = {'url': p['url'], 't': p['t']}
                if p.get('data'):
                    item['data'] = p['data'].copy()
                cls.start_urls.append(item)

    def get_list(self, params: dict):
        ret_list = []

        if params['t'] == 1:
            resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        else:
            resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, data={}, params=params['data'])

        if 400 <= resp.status_code <= 599:
            return ret_list

        soup = BeautifulSoup(resp.text, "html.parser")

        if params['t'] == 1:
            m = re.search(r'<datastore>(.*?)</datastore>', resp.text, re.S)
            script = m.group(1).replace('<![CDATA[', '').replace(']]>', '')
            soup = BeautifulSoup(script, "html.parser")
            rows = soup.select('li')

            for row in rows:
                a_tag = row.select_one('a')
                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                title = a_tag.get_text(strip=True)
                pubTime = row.select_one('span.bt-right').get_text(strip=True)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        if params['t'] == 2:
            rows = soup.select('div.zfxxgk_zdgkc ul li')

            for row in rows:
                a_tag = row.select_one('a')
                url = urljoin('http://wjw.taian.gov.cn/col/col167035/index.html', a_tag.get('href'))
                if not is_same_origin_url(url, 'http://wjw.taian.gov.cn/col/col167035/index.html'):
                    continue

                title = a_tag.get_text(strip=True)
                pubTime = row.select_one('b').get_text(strip=True)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.main-fl > div[style*="text-align:left"]')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
