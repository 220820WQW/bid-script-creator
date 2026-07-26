# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re
import json
import html

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

def extract_memo_html(page_html: str) -> str:
    """
    从页面源码中提取 var memo = "..."，并还原成正常 HTML。
    返回值是可直接渲染的 HTML 字符串。
    """
    m = re.search(
        r'var\s+memo\s*=\s*"((?:\\.|[^"\\])*)"\s*',
        page_html,
        flags=re.S,
    )
    if not m:
        raise ValueError("未找到 memo 字符串")

    memo_escaped = m.group(1)

    # 先按 JS/JSON 字符串规则反转义，\n、\uXXXX、\"、\/ 等都会还原
    memo = json.loads(f'"{memo_escaped}"')

    # 再处理 HTML 实体，比如 &nbsp;、&amp;
    memo = html.unescape(memo)

    # 文章里常见的换行/空白整理，按需保留或删除
    memo = memo.replace("\r\n", "\n").replace("\r", "\n")

    return memo

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
                "url": "http://hezerf.heze.gov.cn/els-service/article/1/15",
                "page_number": 1,
                'data': {
                    "dw": [
                        "2c908088819842f701819a19cc180003"
                    ],
                    "type": [
                        1
                    ],
                    "fwzt": "3",
                    "order": "fwdate",
                    "catas": [
                        "1589462242292797440"
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
            url = f"http://hezerf.heze.gov.cn/{dwid}/{xxid}.html"

            title = row.get('subject')
            pubTime = row.get('fwdate')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        content = extract_memo_html(resp.text)
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
