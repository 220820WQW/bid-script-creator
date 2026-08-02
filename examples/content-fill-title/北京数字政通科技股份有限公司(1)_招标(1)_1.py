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
            # 公司新闻
            {
                "url": "https://www.egova.com.cn/news",
                "page_number": 1,
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append({'url': p['url']})

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select('.news-list-top-img > a, #nw > li a')

        for a_tag in rows:
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            ret_list.append({'url': url, 'title': None, 'pubTime': None})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('.content-in')

        if params['title'] is None:
            params['title'] = soup.select_one('.news-top h2').get_text(strip=True)

        if params['pubTime'] is None:
            pub_time = soup.select_one('.news-top h3').get_text(strip=True)
            params['pubTime'] = handle_str.extract_and_validate_dates(pub_time)[0]

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
