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


HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "http://rfb.yichun.gov.cn",
    "Pragma": "no-cache",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}
COOKIES = {
    "ariaappid": "4dde41e1e986b1b5d7ea404cc9e59433",
    "ariauseGraymode": "false"
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
                "url": "http://rfb.yichun.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "ycsrfb",
                    "channelId[]": "1996819971664617472"
                },
                't': 1
            },
            # 规范性文件
            {
                "url": "http://rfb.yichun.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": 1,
                    "pageSize": 15,
                    "webSiteCode": [
                        "ycsrfb"
                    ],
                    "channelId": [
                        "1996820032029040640"
                    ],
                    "notReturnContent": True
                },
                't': 2
            },
            # 其他有关文件
            {
                "url": "http://rfb.yichun.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": 1,
                    "pageSize": 15,
                    "webSiteCode": [
                        "ycsrfb"
                    ],
                    "channelId": [
                        "1996820033719345152"
                    ],
                    "notReturnContent": True
                },
                't': 2
            },
            # 决策公开
            {
                "url": "http://rfb.yichun.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": 1,
                    "pageSize": 15,
                    "webSiteCode": [
                        "ycsrfb"
                    ],
                    "channelId": [
                        "1996820040426037248"
                    ],
                    "notReturnContent": True
                },
                't': 2
            },
            # 行政许可
            {
                "url": "http://rfb.yichun.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": 1,
                    "pageSize": 15,
                    "webSiteCode": [
                        "ycsrfb"
                    ],
                    "channelId": [
                        "1996820042149896192"
                    ],
                    "notReturnContent": True
                },
                't': 2
            },
            # 行政执法
            {
                "url": "http://rfb.yichun.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": 1,
                    "pageSize": 15,
                    "webSiteCode": [
                        "ycsrfb"
                    ],
                    "channelId": [
                        "1996820043932475392"
                    ],
                    "notReturnContent": True
                },
                't': 2
            },
            # 重点民生项目
            {
                "url": "http://rfb.yichun.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": 1,
                    "pageSize": 15,
                    "webSiteCode": [
                        "ycsrfb"
                    ],
                    "channelId": [
                        "1996820048827228160"
                    ],
                    "notReturnContent": True
                },
                't': 2
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy(), 't': p['t']
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        if params['t'] == 1:
            resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, data=params['data'])
        else:
            headers = HEADERS.copy()
            headers['Content-Type'] = "application/json;charset=UTF-8"
            data = json.dumps(params['data'], separators=(',', ':'))
            resp = auto_request(url=params['url'], headers=headers, cookies=COOKIES, data=data, verify=False)

        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data').get('results')

        for row in rows:
            urls_raw = row.get('source').get('urls')
            urls = json.loads(urls_raw).get('pc')
            url = urljoin("http://rfb.yichun.gov.cn/", urls)
            if not is_same_origin_url(url, params['url']):
                continue

            title = row.get('source').get('title') or row.get('source').get('showTitle')
            pubTime = row.get('source').get('pubDate')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div#zoomcon')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
