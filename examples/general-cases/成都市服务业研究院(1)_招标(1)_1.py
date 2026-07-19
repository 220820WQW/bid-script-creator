# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str


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


HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Authorization;": "",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "http://www.crisi.cn",
    "Pragma": "no-cache",
    "Referer": "http://www.crisi.cn/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "lang": "zh-cn"
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
            # 采购公告
            {
                "url": "http://www.crisi.cn/api/OpenApi/WebSite/GetPageModel",
                "page_number": 1,
                'data': {
                    "page": 1,
                    "limit": 9,
                    "categoryId": "db452321-60eb-4979-a9ba-d2e6fe7a1d5e",
                    "fastKey": ""
                }
            },
            # 通知公告
            {
                "url": "http://www.crisi.cn/api/OpenApi/WebSite/GetPageModel",
                "page_number": 1,
                'data': {
                    "page": 1,
                    "limit": 10,
                    "categoryId": "53fcbf1d-6063-449c-8151-ade80efc4743"
                }
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy()
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, json=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        obj = resp.json().get('data')
        rows = obj.get('data')

        for row in rows:
            articleId = row.get('articleId')
            url = f'http://www.crisi.cn/#/detail/{articleId}'

            title = row.get('title')
            pubTime = row.get('publishTime')

            detail_url = f'http://www.crisi.cn/api/OpenApi/WebSite/Aggregate/{articleId}'
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'detail_url': detail_url})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['detail_url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        obj = resp.json().get('data')
        content = obj.get('contentHtml')

        if attachments := obj.get('attachments'):
            for attach in attachments:
                a = attach.get('fileWebPathName')
                fj_url = f"http://www.crisi.cn/{a}"
                a_tag = f'<a href="{fj_url}">{attach.get("fullName")}</a>'
                content += a_tag

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
