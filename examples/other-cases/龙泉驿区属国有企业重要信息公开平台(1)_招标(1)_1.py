# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bbSpider import Spider, request, handle_str


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
            # 项目招采
            {
                "url": "http://47.109.31.142:9527/api/tender",
                "page_number": 5,
                "data": {
                    "pageSize": 10,
                    "page": 1,
                    "step": "",
                    "name": "",
                    "unit": "",
                },
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                data = p['data'].copy()
                data['page'] = index
                cls.start_urls.append({'url': p['url'], 'data': data})

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], params=params['data'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data').get('items')
        site_url = "http://info.cdjkfz.com/info/project"

        for row in rows:
            article_id = row.get('id')
            url = f"http://info.cdjkfz.com/info/project/detail?id={article_id}"
            if not is_same_origin_url(url, site_url):
                continue

            title = row.get('name').strip()
            pubTime = row.get('createdAt')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': article_id})

        return ret_list

    def get_content(self, params: dict):
        url = f"http://47.109.31.142:9527/api/tender/{params['id']}"
        resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        item = resp.json().get('data')
        soup = BeautifulSoup("", "html.parser")
        content = soup.new_tag('div')

        for file_key, file_name in (
            ('file', '交易公告'),
            ('changeFile', '变更公告'),
            ('failureFile', '流标或终止公告'),
            ('comfirmFile', '评标结果'),
            ('resultFile', '中标公告'),
        ):
            if item.get(file_key):
                p_tag = soup.new_tag('p')
                p_tag.append(soup.new_tag('a', href=urljoin(url, item.get(file_key)), string=file_name))
                content.append(p_tag)

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": str(content)}


if __name__ == "__main__":
    CrawlerObject().start()
