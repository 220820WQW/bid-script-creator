# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str


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
        return hostname.lower().removeprefix("www.")

    if _is_attachment(url_a) or _is_attachment(url_b):
        return False

    domain_a = _get_domain(url_a)
    domain_b = _get_domain(url_b)
    return domain_a == domain_b


# endregion


HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://www.hnlib.com/Info/Detail/15830",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
COOKIES = {
    "acw_tc": "707c9f6217817489190252599e5c95d70c4f3f4f34af9dbc97a4eb12815f81",
    "__51uvsct__JJocKbs3iVQcWwPn": "1",
    "__51vcke__JJocKbs3iVQcWwPn": "bdf3e539-f467-574b-a364-dc70fbbb39e3",
    "__51vuft__JJocKbs3iVQcWwPn": "1781748919199",
    "__vtins__JJocKbs3iVQcWwPn": "%7B%22sid%22%3A%20%227bc0878f-fae7-558f-a788-57215b0b1a01%22%2C%20%22vd%22%3A%203%2C%20%22stt%22%3A%20646151%2C%20%22dr%22%3A%20635565%2C%20%22expires%22%3A%201781751365345%2C%20%22ct%22%3A%201781749565345%7D"
}


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 本馆公告
            {
                "url": "https://www.hnlib.com/Info/GetList/1?pageNum=1&size=12",
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

        rows = resp.json().get('list')

        for row in rows:
            Url = row.get('Url')
            url = urljoin(params['url'], Url)
            if not is_same_origin_url(url, params['url']):
                continue

            title = row.get('Title')
            pubTime = row.get('ShowDate')
            Id = row.get('Id')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'Id': Id})

        return ret_list

    def get_content(self, params: dict):
        u = f'https://www.hnlib.com/Info/GetDetail/{params["Id"]}?pageNum=&size=6'
        resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        obj = resp.json().get('detail')
        content = obj.get('Content')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
