# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import random


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

MOBILE_BROWSER_UA = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/21F79 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/21E236 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/21D61 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/21C66 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/21B101 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/21F79 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/21E236 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/21D61 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/21C66 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/21B101 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/21F79 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/21E236 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/21D61 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/21C66 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/21B101 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/21F79 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/21E236 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/21D61 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/21C66 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/21B101 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.8 Mobile/21F79 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.8 Mobile/21E236 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.8 Mobile/21D61 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.8 Mobile/21C66 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.8 Mobile/21B101 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/126.0.6478.54 Mobile/21F79 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/125.0.6422.80 Mobile/21E236 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/124.0.6367.60 Mobile/21D61 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/123.0.6312.122 Mobile/21C66 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/122.0.6261.128 Mobile/21B101 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/121.0.6167.101 Mobile/21F79 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/121.0.6167.101 Mobile/21E236 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/121.0.6167.101 Mobile/21D61 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/121.0.6167.101 Mobile/21C66 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/121.0.6167.101 Mobile/21B101 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.216 Mobile/21F79 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.216 Mobile/21E236 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.216 Mobile/21D61 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.216 Mobile/21C66 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.216 Mobile/21B101 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.147 Mobile/21F79 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.147 Mobile/21E236 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.147 Mobile/21D61 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.147 Mobile/21C66 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.147 Mobile/21B101 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/127.0 Mobile/21F79 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/126.0 Mobile/21E236 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/125.0 Mobile/21D61 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/124.0 Mobile/21C66 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/123.0 Mobile/21B101 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/122.0 Mobile/21F79 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/122.0 Mobile/21E236 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/122.0 Mobile/21D61 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/122.0 Mobile/21C66 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/122.0 Mobile/21B101 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/121.0 Mobile/21F79 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/121.0 Mobile/21E236 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/121.0 Mobile/21D61 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/121.0 Mobile/21C66 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/121.0 Mobile/21B101 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.126 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.126 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.126 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.126 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; M2102K1C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.126 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; CPH2531) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; V2219A) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; Pixel 6 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; RMX3551) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; 22041216G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.99 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 11; SM-A525F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.99 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 11; M2007J20CG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.99 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 11; V2043A) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.99 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 11; XQ-BC72) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.99 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 10; Pixel 4 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.128 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 10; SM-N975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.128 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 10; M2006C3LG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.128 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 10; ANE-LX1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.128 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 10; ELZ-AN00) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.128 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.126 Mobile Safari/537.36 SamsungBrowser/24.0',
    'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.126 Mobile Safari/537.36 SamsungBrowser/24.0',
    'Mozilla/5.0 (Linux; Android 13; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36 SamsungBrowser/23.0',
    'Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36 SamsungBrowser/23.0',
    'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36 SamsungBrowser/22.0',
    'Mozilla/5.0 (Android 14; Mobile; Pixel 8 Pro) Gecko/127.0 Firefox/127.0',
    'Mozilla/5.0 (Android 13; Mobile; Pixel 7) Gecko/126.0 Firefox/126.0',
    'Mozilla/5.0 (Android 13; Mobile; SM-S918B) Gecko/126.0 Firefox/126.0',
    'Mozilla/5.0 (Android 12; Mobile; M2012K11AC) Gecko/125.0 Firefox/125.0',
    'Mozilla/5.0 (Android 11; Mobile; SM-A525F) Gecko/124.0 Firefox/124.0',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.2592.87 Mobile Safari/537.36 EdgA/126.0.2592.87',
    'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.2592.87 Mobile Safari/537.36 EdgA/126.0.2592.87',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.2535.79 Mobile Safari/537.36 EdgA/125.0.2535.79',
    'Mozilla/5.0 (Linux; Android 12; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.2535.79 Mobile Safari/537.36 EdgA/125.0.2535.79',
    'Mozilla/5.0 (Linux; Android 11; M2007J20CG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.2478.52 Mobile Safari/537.36 EdgA/124.0.2478.52'
]

HEADERS = {
    # "user-agent": "Mozilla/5.0 (Linux; IOS 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Mobile Safari/537.36",
    "referer": "https://www.hhnycg.com/cms/channel/ywgg1qb/index.htm",
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
            # 公告
            {"url": "https://www.hhnycg.com/cms/channel/ywgg1qb/index.htm?pageNo={}",
             "page_number": 20},
            # 资格预审 暂无数据
            {"url": "https://www.hhnycg.com/cms/channel/ywgg6qb/index.htm?pageNo={}",
             "page_number": 1},
            # 中标候选人公示
            {"url": "https://www.hhnycg.com/cms/channel/ywgg3qb/index.htm?pageNo={}",
             "page_number": 20},
            # #  中标结果公告
            {"url": "https://www.hhnycg.com/cms/channel/ywgg5qb/index.htm?pageNo={}",
             "page_number": 20},
            # 变更
            {"url": "https://www.hhnycg.com/cms/channel/ywgg7qb/index.htm?pageNo={}",
             "page_number": 20},
            # 终止
            {"url": "https://www.hhnycg.com/cms/channel/ywgg8qb/index.htm?pageNo={}",
             "page_number": 10},
            # 合同
            {"url": "https://www.hhnycg.com/cms/channel/ywgg9qb/index.htm?pageNo={}",
             "page_number": 10},
            # 询价
            {"url": "https://www.hhnycg.com/cms/channel/ywgg2qb/index.htm?pageNo={}",
             "page_number": 25},
            # 竞争性谈判
            {"url": "https://www.hhnycg.com/cms/channel/ywgg10qb/index.htm?pageNo={}",
             "page_number": 1},
            # 竞价 暂无数据
            {"url": "https://www.hhnycg.com/cms/channel/ywgg11qb/index.htm?pageNo={}",
             "page_number": 1},
            # 拟单一来源公示
            {"url": "https://www.hhnycg.com/cms/channel/ywgg12qb/index.htm?pageNo={}",
             "page_number": 15},
            # 成交候选人公示
            {"url": "https://www.hhnycg.com/cms/channel/ywgg13qb/index.htm?pageNo={}",
             "page_number": 1},
            # 成交结果
            {"url": "https://www.hhnycg.com/cms/channel/ywgg4qb/index.htm?pageNo={}",
             "page_number": 80},
            # 变更
            {"url": "https://www.hhnycg.com/cms/channel/ywgg15qb/index.htm?pageNo={}",
             "page_number": 5},
            # 终止
            {"url": "https://www.hhnycg.com/cms/channel/ywgg14qb/index.htm?pageNo={}",
             "page_number": 20},
            # # 招采计划公告 暂无数据
            {"url": "https://www.hhnycg.com/cms/channel/0ywgg/index.htm?pageNo={}",
             "page_number": 1},
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'].format(index),
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        headers = HEADERS.copy()
        headers['user-agent'] = random.choice(MOBILE_BROWSER_UA)

        resp = auto_request(url=params['url'], headers=headers, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select('ul#list1 li')

        for row in rows:
            a_tag = row.select_one('a')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.get('title')
            if not title:
                span = a_tag.select_one(':scope > span')
                if i := span.select_one('i'):
                    i.decompose()
                if em := span.select_one("em"):
                    em.decompose()
                title = span.get_text(strip=True)

            pubTime = row.select_one('a > em').get_text(strip=True)
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        headers = HEADERS.copy()
        headers['user-agent'] = random.choice(MOBILE_BROWSER_UA)

        resp = auto_request(url=params['url'], headers=headers, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.main-text')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
