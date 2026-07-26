# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
from functools import partial
import subprocess
subprocess.Popen = partial(subprocess.Popen, encoding="utf-8")

import execjs


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
        return hostname.lower().removeprefix("www.")

    if _is_attachment(url_a) or _is_attachment(url_b):
        return False

    domain_a = _get_domain(url_a)
    domain_b = _get_domain(url_b)
    return domain_a == domain_b


HEADERS = {}
COOKIES = {}


def get_list(text):
    js_code = "function cmd(text) {eval(text);return PAGE_INDEX_MAP543;}"
    res = execjs.compile(js_code).call('cmd', text)
    return res


def get_cont(text):
    js_code = "function cmd(text) {eval(text);return MI4_PAGE_ARTICLE;}"
    res = execjs.compile(js_code).call('cmd', text)
    return res


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 通知公告
            {
                "url": "https://www.tass-tj.org.cn/js/543/mi4_page_articles_guide.js?20260430190052",
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

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        js_list = get_list(resp.text)
        for k, v in js_list.items():
            if k.isdigit():
                u = f"https://www.tass-tj.org.cn/js/543/{v}?v=20260430190052"

                resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES)
                if 400 <= resp.status_code <= 599:
                    continue

                js_cont = get_cont(resp.text)
                title = js_cont[0].get('title')
                pubTime = js_cont[0].get('pub_date')
                url = js_cont[0].get('url')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.content_dt_con')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
