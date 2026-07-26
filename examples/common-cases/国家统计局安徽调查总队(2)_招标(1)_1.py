# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str


# region fixed methods
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
            # 通知通告
            {
                "url": "http://ahzd.stats.gov.cn/ahdcweb/web/upGrade/columnIfmList",
                "page_number": 1,
                "data": {
                    "strId": "d0abcda920e940ea8aff5b958ebb3af5",
                    "intCurPage": 1,
                    "intPageSize": 15
                }
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                data = p['data'].copy()
                data['intCurPage'] = index
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': data
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, json=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('map').get('dataList')

        for row in rows:
            id = row.get('strId')
            if row.get('strEditType') == 'url':
                url = urljoin(
                    "http://ahzd.stats.gov.cn/#/news/index3?id=d0abcda920e940ea8aff5b958ebb3af5&strType=1&menuType=1",
                    row.get('strHtmlUrl')
                )
            else:
                url = urljoin(
                    "http://ahzd.stats.gov.cn/#/news/index3?id=d0abcda920e940ea8aff5b958ebb3af5&strType=1&menuType=1",
                    f"/#/details?id={id}"
                )
            if not is_same_origin_url(url, "http://ahzd.stats.gov.cn/#/news/index3?id=d0abcda920e940ea8aff5b958ebb3af5&strType=1&menuType=1"):
                continue

            title = row.get('strMasTitle')
            pubTime = row.get('strPubDate')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(
            url="http://ahzd.stats.gov.cn/ahdcweb/web/upGrade/view",
            headers=HEADERS,
            cookies=COOKIES,
            json={"strId": params['id']}
        )
        if 400 <= resp.status_code <= 599:
            return None

        content = resp.json().get('map').get('info').get('strContent')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
