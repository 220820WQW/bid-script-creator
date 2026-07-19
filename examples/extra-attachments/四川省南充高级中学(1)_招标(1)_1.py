# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import json


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


HEADERS = {}
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
            # 学校公告
            {
                "url": "https://www.scncgz.net/prod-api/webpage/content/listContent?menuId=1078&pageNum=1&pageSize=10",
                "page_number": 1,
            },
            # 会务公开
            {
                "url": "https://www.scncgz.net/prod-api/webpage/content/listContent?pageSize=10&pageNum=1&menuId=1128",
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

        rows = resp.json().get('rows')

        for row in rows:
            id = row.get('id')
            url = f"https://www.scncgz.net/Articledetails?detailId={id}&id=1076"

            title = row.get('title')
            pubTime = row.get('createTime')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id})

        return ret_list

    def get_content(self, params: dict):
        url = f"https://www.scncgz.net/prod-api/webpage/content/contentInfo/{params['id']}"
        resp = auto_request(url, headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        obj = resp.json().get('data')
        content = obj.get('content')

        if fileInfo := obj.get('fileInfo'):
            file_list = json.loads(fileInfo)
            for file in file_list:
                a_tag = f'<a href="{file.get("url")}">{file.get("originalFilename")}</a>'
                content += a_tag

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
