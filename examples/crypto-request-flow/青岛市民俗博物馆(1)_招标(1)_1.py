# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import json
import re


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
    "Origin": "http://www.qdcybhzx.cn",
    "Pragma": "no-cache",
    "Referer": "http://www.qdcybhzx.cn/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}
COOKIES = {
    "current_page_id": "137009",
    "website_id": "89216",
    "website_fid": "179190",
    "website_fid_login": "0",
    "mh_sign": "4ac9ef0666f9a22e971535a8bdc7c4a43b97802742f17d093e8c7efa0b2cf3e2",
    "goc": "o"
}


def extract_balanced_braces(text, open_brace_pos):
    """
    从 text[open_brace_pos] 这个 '{' 开始，提取完整的 {...}
    """
    if text[open_brace_pos] != '{':
        raise ValueError("open_brace_pos must point to '{'")

    depth = 0
    in_string = False
    quote_char = None
    escape = False

    for i in range(open_brace_pos, len(text)):
        ch = text[i]

        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote_char:
                in_string = False
            continue

        if ch == '"' or ch == "'":
            in_string = True
            quote_char = ch
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[open_brace_pos:i + 1]

    raise ValueError("Unbalanced braces")


def extract_vue_inner_data(html_text):
    """
    提取 Vue 里 data 对象中的内层 data 字段。
    返回 Python dict。
    """
    # 1) 找外层 Vue 的 data: {
    m_outer = re.search(r'\bdata\s*:\s*\{', html_text)
    if not m_outer:
        raise ValueError("outer Vue data block not found")

    outer_block = extract_balanced_braces(html_text, m_outer.end() - 1)

    # 2) 在外层 block 里找内层 data: {
    m_inner = re.search(r'\bdata\s*:\s*\{', outer_block)
    if not m_inner:
        raise ValueError("inner data object not found")

    inner_block = extract_balanced_braces(outer_block, m_inner.end() - 1)

    # 3) 内层本身是 JSON 风格，直接解析
    return json.loads(inner_block)


def get_sign():
    for _ in range(8):
        url = "http://www.qdcybhzx.cn/engine2/general/more?t=D283B63FCAA8E68725013CC05C77047358C2DE6A8A9731DE950F47BF382321BD784BA85A59A5CF3B50A88391EF6FCAF4"
        resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES)
        if resp.status_code != 200:
            continue

        m = re.search('sign = "(.*?)";', resp.text)
        return m.group(1)
    else:
        return None


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
                "url": "http://www.qdcybhzx.cn/engine2/general/774963/type/more-datas",
                "page_number": 3,
                'data': {
                    "engineInstanceId": "984287",
                    "sign": "",
                    "pageNum": "3",
                    "pageSize": "15",
                    "typeId": "6246138",
                    "topTypeId": "",
                    "sw": "",
                    "relId": "",
                    "startDate": "",
                    "endDate": "",
                    "typeDataSort": "-1",
                    "letter": ""
                }
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                p['data']['pageNum'] = str(index)
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy()
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        sign = get_sign()
        if sign is None:
            return ret_list

        params['data']['sign'] = sign

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, data=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        obj = resp.json().get('data').get('datas')
        rows = obj.get('datas')

        for row in rows:
            url = row.get('url')
            url = urljoin(params['url'], url)
            if not is_same_origin_url(url, params['url']):
                continue

            title = row.get('title')
            pubTime = row.get('publishTime')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        m = re.search(r'logoutUrl = "(.*?)";', resp.text)
        u = m.group(1).replace('\\', '').replace('u0026', '&')
        url = f"http://www.qdcybhzx.cn{u}"

        resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        obj = extract_vue_inner_data(resp.text)
        content = obj.get('content')

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
