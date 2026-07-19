# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re
import execjs
from bbSpider.agent_pool import agent_pool
import hashlib
import json


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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Host": "sthjt.jiangsu.gov.cn",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
}
COOKIES = {}


def _extract_go_object(js_text):
    idx = js_text.rfind("go(")
    if idx < 0:
        raise ValueError("go(...) not found")

    start = js_text.find("{", idx)
    if start < 0:
        raise ValueError("go object start not found")

    depth = 0
    in_str = None
    esc = False
    for i in range(start, len(js_text)):
        ch = js_text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            continue

        if ch in ("'", '"'):
            in_str = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return js_text[start: i + 1]

    raise ValueError("go object end not found")


def _load_config(js_text):
    raw = _extract_go_object(js_text)
    return json.loads(raw)


def _digest(name, text):
    data = text.encode("utf-8")
    if name == "md5":
        return hashlib.md5(data).hexdigest()
    if name == "sha1":
        return hashlib.sha1(data).hexdigest()
    if name == "sha256":
        return hashlib.sha256(data).hexdigest()
    raise ValueError("unsupported hash: %s" % name)


def _solve_cookie(cfg):
    bts0, bts1 = cfg["bts"]
    chars = cfg["chars"]
    ct = cfg["ct"]
    ha = cfg["ha"].lower()

    for a in chars:
        for b in chars:
            candidate = bts0 + a + b + bts1
            if _digest(ha, candidate) == ct:
                return candidate

    raise ValueError("cookie not found")


def extract_cookie(js_text):
    cfg = _load_config(js_text)
    value = _solve_cookie(cfg)
    return {
        "cookie_name": cfg["tn"],
        "cookie_value": value,
        "cookie": "%s=%s" % (cfg["tn"], value),
    }


def get_headers(url, proxies):
    for _ in range(5):
        resp = auto_request(url=url, headers=HEADERS, proxies=proxies)
        if resp.status_code != 521:
            continue

        m = re.search(r'document\.(.*?);location', resp.text)
        js_code = "function cmd(code) {eval(code);return cookie}"
        res = execjs.compile(js_code).call('cmd', m.group(1))

        cookies = ''
        for k, v in resp.cookies.items():
            cookies += f'{k}={v}; '

        c1 = cookies + res
        headers = HEADERS.copy()
        headers['Cookie'] = c1

        resp = auto_request(url=url, headers=headers, proxies=proxies)
        if resp.status_code != 521:
            continue

        result = extract_cookie(resp.text)
        # print(result["cookie"])
        c2 = cookies + result['cookie']
        headers['Cookie'] = c2

        return headers
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
            # 公示公告 IP被封 加速乐
            {
                "url": "http://www.nsfz.net/xwzx/tzgg",
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

        proxies = agent_pool(params['url'])[urlparse(params['url']).scheme]
        headers = get_headers(params['url'], proxies)
        if headers is None:
            return ret_list

        resp = auto_request(url=params['url'], headers=headers, cookies=COOKIES, proxies=proxies)
        if 400 <= resp.status_code <= 599:
            return ret_list

        soup = BeautifulSoup(resp.text, "html.parser")
        wrap = soup.select_one('ul.newsList')
        rows = wrap.select('li') if wrap else []

        for row in rows:
            a_tag = row.select_one('a')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.get_text(strip=True)
            pubTime = row.select_one('span').get_text(strip=True)
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'headers': headers})

        return ret_list

    def get_content(self, params: dict):
        proxies = agent_pool(params['url'])[urlparse(params['url']).scheme]
        headers = get_headers(params['url'], proxies)
        if headers is None:
            return None

        resp = auto_request(url=params['url'], headers=headers, cookies=COOKIES, proxies=proxies)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.conTxt')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
