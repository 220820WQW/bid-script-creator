# -*- coding: UTF-8 -*-
import ast
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


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/132 Safari/537.36",
}
COOKIES = {}


def get_document_soup(url):
    resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES)
    if 400 <= resp.status_code <= 599:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    resp = auto_request(
        url=soup.select_one('#smart-body > script').get('src'),
        headers=HEADERS,
        cookies=COOKIES,
    )
    if 400 <= resp.status_code <= 599:
        return None

    return BeautifulSoup(ast.literal_eval(resp.text[15:-2]), "html.parser")


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 企务公开
            {
                "url": "https://www.btjttz.com/qwgk",
                "page_number": 1,
            },
            # 通知通告
            {
                "url": "https://www.btjttz.com/tztg",
                "page_number": 1,
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append({'url': p['url']})

    def get_list(self, params: dict):
        ret_list = []

        soup = get_document_soup(params['url'])
        if soup is None:
            return ret_list

        rows = soup.select('#ulList_con_18_56 > li')

        for row in rows:
            a_tag = row.select_one('a.w-list-titlelink')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.get_text(strip=True)
            pubTime = row.select_one('span.w-list-date').get_text(strip=True)
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        soup = get_document_soup(params['url'])
        if soup is None:
            return None

        content = soup.select_one('div.w-detail')
        content = handle_str.completion_url(str(content), params['url'])

        return {
            "title": params['title'],
            "pubTime": params['pubTime'],
            "url": params['url'],
            "content": content,
        }


if __name__ == "__main__":
    CrawlerObject().start()
