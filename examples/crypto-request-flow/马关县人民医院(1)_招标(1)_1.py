# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re
from bbSpider.agent_pool import agent_pool
import random


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
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8,"
        "application/signed-exchange;v=b3;q=0.7"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "sec-ch-ua": '"Chromium";v="126", "Google Chrome";v="126", ";Not A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}
COOKIES = {}


def to_hex(text):
    return "".join(format(ord(ch), "x") for ch in text)


def get_headers(url, proxies):
    first = auto_request(url=url, headers=HEADERS, cookies=COOKIES, allow_redirects=False, proxies=proxies)
    if 400 <= first.status_code <= 599:
        return None

    m_verify = re.search(r"security_session_verify=([0-9a-f]+)", first.headers.get("Set-Cookie", ""))
    headers = HEADERS.copy()
    headers = {
        **headers,
        "Referer": url,
        "Cookie": f"security_session_verify={m_verify.group(1)}",
    }

    mid_candidates = ["1366,768", "1920,1080", "1536,864", "1440,900", "1600,900"]
    second_url = f"{url}?security_verify_data={to_hex(random.choice(mid_candidates))}"

    second = auto_request(url=second_url, headers=headers, cookies=COOKIES, allow_redirects=False, proxies=proxies)
    if 400 <= first.status_code <= 599:
        return None

    m_mid = re.search(
        r"security_session_mid_verify=([0-9a-f]+)",
        second.headers.get("Set-Cookie", ""),
    )
    if not m_mid:
        return None

    out_headers = {
        **headers,
        "Referer": url,
        "Cookie": (
            f"security_session_verify={m_verify.group(1)}; "
            f"security_session_mid_verify={m_mid.group(1)}"
        ),
    }
    return out_headers


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
                "url": "http://mgxrmyy.com.cn/cnPc/tzgg/index.html",
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

        for _ in range(10):
            proxies = agent_pool(params['url'])[urlparse(params['url']).scheme]
            headers = get_headers(params['url'], proxies)
            if headers is None:
                continue
            break
        else:
            return ret_list

        resp = auto_request(url=params['url'], headers=headers, cookies=COOKIES, proxies=proxies)
        if 400 <= resp.status_code <= 599:
            return ret_list

        soup = BeautifulSoup(resp.text, "html.parser")
        wrap = soup.select_one('dl.imgText4')
        rows = wrap.select('dd') if wrap else []

        for row in rows:
            a_tag = row.select_one('.title > a')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.get_text(strip=True)
            pubTime = row.select_one('.time').get_text(strip=True)
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        for _ in range(10):
            proxies = agent_pool(params['url'])[urlparse(params['url']).scheme]
            headers = get_headers(params['url'], proxies)
            if headers is None:
                continue
            break
        else:
            return None

        resp = auto_request(url=params['url'], headers=headers, cookies=COOKIES, proxies=proxies)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div#articleContent')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
