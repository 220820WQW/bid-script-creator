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
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "http://safety.jian.gov.cn",
    "Pragma": "no-cache",
    "Referer": "http://safety.jian.gov.cn/xxgk-list-jhybteawbtlp.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}
COOKIES = {
    "HWWAFSESID": "94ea97f6c5a0c93293",
    "HWWAFSESTIME": "1783563221535",
    "CI35DFF8B91D80B5_ci_session": "efqbpjcj6ce62fejdh00fap86ddd2lha"
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
            # 建议提案办理
            {
                "url": "http://safety.jian.gov.cn/api-ajax_list-1.html",
                "page_number": 1,
                'data': {
                    "ajax_type[]": [
                        "49_xxgk",
                        "165775",
                        "49",
                        "xxgk",
                        "Y-m-d",
                        "50",
                        "20",
                        ""
                    ],
                    "ajax_type[7][]": [
                        "is_top DESC",
                        "displayorder DESC",
                        "inputtime DESC"
                    ],
                    "is_ds": "1"
                }
            },
            # 安全生产
            {
                "url": "http://safety.jian.gov.cn/api-ajax_list-1.html",
                "page_number": 1,
                'data': {
                    "ajax_type[]": [
                        "49_xxgk",
                        "165807",
                        "49",
                        "xxgk",
                        "Y-m-d",
                        "50",
                        "20",
                        ""
                    ],
                    "ajax_type[7][]": [
                        "is_top DESC",
                        "displayorder DESC",
                        "inputtime DESC"
                    ],
                    "is_ds": "1"
                }
            },
            # 决策公开
            {
                "url": "http://safety.jian.gov.cn/api-ajax_list-1.html",
                "page_number": 1,
                'data': {
                    "ajax_type[]": [
                        "49_xxgk",
                        "165738",
                        "49",
                        "xxgk",
                        "Y-m-d",
                        "50",
                        "20",
                        ""
                    ],
                    "ajax_type[7][]": [
                        "is_top DESC",
                        "displayorder DESC",
                        "inputtime DESC"
                    ],
                    "is_ds": "1"
                }
            },
            # 政策文件
            {
                "url": "http://safety.jian.gov.cn/api-ajax_list-1.html",
                "page_number": 1,
                'data': {
                    "ajax_type[]": [
                        "49_xxgk",
                        "10421",
                        "49",
                        "xxgk",
                        "Y-m-d",
                        "50",
                        "20",
                        ""
                    ],
                    "ajax_type[7][]": [
                        "is_top DESC",
                        "displayorder DESC",
                        "inputtime DESC"
                    ],
                    "is_ds": "1"
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

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, data=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data')

        for row in rows:
            url = row.get('url')
            if not is_same_origin_url(url, params['url']):
                continue

            title = row.get('title')
            pubTime = row.get('inputtime')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.xxgk_content')

        if iframe_tag := content.select_one('iframe'):
            a_tag = soup.new_tag(name='a', href=iframe_tag.get('src'), string="内容附件")
            content.append(a_tag)

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
