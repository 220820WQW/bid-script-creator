# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re
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


HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "http://wfsj.weifang.gov.cn",
    "Pragma": "no-cache",
    "Referer": "http://wfsj.weifang.gov.cn/sjjlist/?ch=%E9%80%9A%E7%9F%A5%E5%85%AC%E5%91%8A",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "msstoken": "oVsUBhj1dx5gy3R8YutDHR1gyyBafqfsyi9JQnnIk3PmZPGbNDYxo50GDAOmvnuBzfZkMVpP+SoUG7eC0Kfdax2/9Q5CX/Ea6DFN2cLJHrw=",
    "mstoken": "KUEfi1LxzelSjDtf6EQLq/OGJ7YFcEQ0P8MupmSJYX9u1jJBn8ftCwBO8maiCqB+ZXvIJMVSM/sPL81bOdnr9FOSRBJGZ1n8C9hllAho5mA="
}
COOKIES = {
    "lk_behavior___static_process_key": "spk_17835045087841003709b9d678d84485",
    "lk_behavior__weiFangGovweb-weifang-sjj__process_key": "pk_178350450878510012b5164431aa29cd",
    "lk_behavior__weiFangGovweb-weifang-sjj__process_push_index": "3",
    "lk_behavior__weiFangGovweb-weifang-sjj__process_operate_time": "1783504536086"
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
            # 通知公告
            {
                "url": "http://wfsj.weifang.gov.cn/els-service/article/1/15",
                "page_number": 1,
                'data': {
                    "dq": "162",
                    "dw": [
                        "55350"
                    ],
                    "catas": [
                        "1712635726480412672"
                    ]
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

        rows = resp.json().get('data').get('contents')

        for row in rows:
            dwid = row.get('dwid')
            xxid = row.get('xxid')
            url = f"http://wfsj.weifang.gov.cn/{dwid}/{xxid}.html"

            title = row.get('subject')
            pubTime = row.get('fwdate')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        m = re.search(r'var memo =  "(.*)"', resp.text)
        content = json.loads(f'"{m.group(1)}"')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
