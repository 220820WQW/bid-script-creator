# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse, unquote

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str

import re
import json
import base64


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


HEADERS = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://scqlib.mh.chaoxing.com",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://scqlib.mh.chaoxing.com/",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}
COOKIES = {
    "current_page_id": "282742",
    "website_id": "164649",
    "website_fid": "10473",
    "website_fid_login": "0",
    "mh_sign": "97a32601677bf3a751cd885a7c59235e5b3d3d49a7a4ccf9d65a1ce9ecfa1bad",
    "browserLocale": "zh_CN",
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
    url = "https://scqlib.mh.chaoxing.com/engine2/general/more?appId=1477126&wfwfid=10473&pageId=282742&websiteId=164649&currentBranch=0&typeId=5044364&currentBranch=0"
    resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES)

    m = re.search('sign = "(.*?)";', resp.text)
    return m.group(1)


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 馆内公告
            {
                "url": "https://scqlib.mh.chaoxing.com/engine2/general/1477126/type/more-datas",
                "page_number": 1,
                'data': {
                    "engineInstanceId": "2115462",
                    "sign": "",
                    "pageNum": "1",
                    "pageSize": "20",
                    "typeId": "5044364",
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
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy()
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        sign = get_sign()
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
        url = f"https://scqlib.mh.chaoxing.com{u}"

        resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        obj = extract_vue_inner_data(resp.text)
        content = obj.get('content')

        if "iframe" in content:
            m = re.search(r'name="(.*?)"', content)
            if m:
                d = base64.b64decode(m.group(1)).decode('utf8')
                e = unquote(d)
                f = json.loads(e)
                fileId = f.get('att_clouddisk').get('fileId')

                fj_url = f"https://previewyd.chaoxing.com/pc/view/preview?objectid={fileId}&puid=&download=&enc=&resid=&type="
                resp = auto_request(url=fj_url, headers=HEADERS, cookies=COOKIES)
                if 400 <= resp.status_code <= 599:
                    return None

                data = resp.json().get('data')
                content += f'<a href="{data.get("pdf")}">{data.get("filename")}</a>'

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
