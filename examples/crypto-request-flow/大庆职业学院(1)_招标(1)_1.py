# -*- coding: UTF-8 -*-
import json
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bbSpider import Spider, request, handle_str
import re


# region fixed methods
def auto_request(
        url, params=None, data=None, json=None, proxy_safety=None, **kwargs
):
    if proxy_safety is None:
        proxy_safety = urlparse(url).scheme

    if data is not None or json is not None:
        resp = request.post(
            url,
            params=params,
            data=data,
            json=json,
            proxy_safety=proxy_safety,
            **kwargs,
        )
    else:
        resp = request.get(
            url,
            params=params,
            proxy_safety=proxy_safety,
            **kwargs,
        )

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


HEADERS = {"User-Agent": "Mozilla/5.0"}
COOKIES = {}


def get_sign():
    for _ in range(8):
        resp = auto_request(url="https://www.dqzyxy.net/engine2/m/0/5087079/6076523?p=994443", headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            continue

        sign = re.search(r'sign = "(.*?)";', resp.text).group(1)
        return sign
    else:
        return None


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 学院要闻
            {
                "url": "https://www.dqzyxy.net/engine2/general/5087079/type/more-datas",
                "page_number": 1,
                "data": {
                    "engineInstanceId": "6076523",
                    "sign": "07f7608d4f8ddc6af627c0a6168c89a0",
                    "pageNum": 1,
                    "pageSize": 20,
                    "typeId": "12160983",
                    "topTypeId": "",
                    "sw": "",
                    "relId": "",
                    "startDate": "",
                    "endDate": "",
                    "typeDataSort": -1,
                    "letter": "",
                },
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                data = p['data'].copy()
                data['pageNum'] = index
                cls.start_urls.append({'url': p['url'], 'data': data})

    def get_list(self, params: dict):
        ret_list = []

        sign = get_sign()
        if sign is None:
            return None

        params['data']['sign'] = sign

        resp = auto_request(url=params['url'], data=params['data'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data').get('datas').get('datas')
        site_url = "https://www.dqzyxy.net/engine2/m/0/5087079/6076523?p=994443"

        for row in rows:
            url = f"https://www.dqzyxy.net/engine2/d/{row.get('id')}/6076523/0/5087079?t=12160983&p=994443"
            if not is_same_origin_url(url, site_url):
                continue

            ret_list.append({'url': url, 'title': row.get('title'), 'pubTime': row.get('publishTime')})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        script = soup.find('script', string=lambda text: text and 'detailVue = new Vue' in text)
        content = json.loads(re.search(r'"content":("(?:\\.|[^"\\])*")', script.string).group(1))
        content = handle_str.completion_url(content, params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
