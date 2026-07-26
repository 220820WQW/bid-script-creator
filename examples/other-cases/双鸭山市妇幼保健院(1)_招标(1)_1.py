# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import time
import random
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
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://www.sysfybjy.org.cn/NewsList/2.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}
COOKIES = {
    "Lang": "cn",
    "InitSiteID": "75353",
    "count_clientid": "f6174119a94cb8fbe30034ad6b4ff4f6"
}


def get_CsrfTokenP():
    for attempt in range(8):
        resp = request.get("https://www.sysfybjy.org.cn/", headers=HEADERS)
        cookies = resp.cookies.get_dict()

        resp = request.get(url="https://www.sysfybjy.org.cn/count?Referer=&Width=1920&Height=1080&Page=/", headers=HEADERS, cookies=cookies)
        if resp.status_code != 200:
            wait = min(60, 2 + attempt * 2)
            time.sleep(wait + random.uniform(0.2, 0.8))
            continue

        cookies.update(resp.cookies.get_dict())
        if "CsrfTokenP" not in cookies:
            continue

        return cookies
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
            # 最新公告
            {
                "url": "https://www.sysfybjy.org.cn/index.php?c=Front/LoadModulePageData&ClassID=2&responseModuleId=598240237&PageNo=1",
                "page_number": 1,
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'],
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        cookies = get_CsrfTokenP()
        if cookies is None:
            return []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=cookies, proxy_safety='https')
        if 400 <= resp.status_code <= 599:
            return ret_list

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select('ul.news-container li')

        for row in rows:
            a_tag = row.select_one('a')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.select_one('.news-title').get_text(strip=True)
            pubTime = row.select_one('time').get_text(strip=True)
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'cookies': cookies})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=params['cookies'], proxy_safety='https')
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('#readMore')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
