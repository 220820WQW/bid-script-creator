# -*- coding: UTF-8 -*-
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
from bbSpider.agent_pool import agent_pool
import requests


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
        if hostname.startswith("www."):
            hostname = hostname[4:]
        return hostname

    if _is_attachment(url_a) or _is_attachment(url_b):
        return False

    domain_a = _get_domain(url_a)
    domain_b = _get_domain(url_b)
    return domain_a == domain_b


# endregion


HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
}
COOKIES = {}
session = requests.Session()


def to_hex(text):
    return "".join(format(ord(ch), "x") for ch in text)


def get_text(url, proxies=None):
    first = session.get(url=url, headers=HEADERS, cookies=COOKIES, allow_redirects=False, proxies=proxies)
    if 400 <= first.status_code <= 599:
        return None

    verify = first.cookies.get("security_session_verify")

    headers = HEADERS.copy()
    headers["Cookie"] = f"security_session_verify={verify}; srcurl={to_hex(url)}"
    headers['Referer'] = url

    mid_url = f"{url}?security_verify_data={to_hex('1920,1080')}"
    second = session.get(mid_url, headers=headers, allow_redirects=False, verify=False, proxies=proxies)
    if 400 <= second.status_code <= 599:
        return None

    mid_verify = second.cookies.get("security_session_mid_verify")
    headers['Cookie'] = f"{headers['Cookie']}; security_session_mid_verify={mid_verify}"

    third = session.get(url, headers=headers, allow_redirects=False, verify=False, proxies=proxies)
    third.encoding = 'utf-8'
    if "security_verify_data" in third.text:
        return None
    return third.text


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
                "url": "https://limingpuer.com/list/cnIndex/1/195/auto/12/0.html",
                "page_number": 1,
            },
        )

        for p in payload_list:
            for index in range(1, p["page_number"] + 1):
                cls.start_urls.append(
                    {
                        "url": p["url"],
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        for _ in range(8):
            proxies = agent_pool(params['url'])['https']
            text = get_text(params["url"], proxies)
            if text is None:
                continue
            break
        else:
            return ret_list

        # resp = auto_request(url=params["url"], headers=headers, cookies=COOKIES, proxies=proxies)
        # if 400 <= resp.status_code <= 599:
        #     return ret_list

        soup = BeautifulSoup(text, "html.parser")
        rows = soup.select("dl.textImg1 dd")

        for row in rows:
            a_tag = row.select_one("a.list_a")
            url = urljoin(params["url"], a_tag.get("href"))
            if not is_same_origin_url(url, "https://limingpuer.com/list/cnIndex/1/195/auto/12/0.html"):
                continue

            title = a_tag.select_one("div.listName").get_text(strip=True)
            pubTime = a_tag.select_one("div.listTime").get_text(strip=True)
            pubTime = handle_str.extract_and_validate_dates(pubTime)[0]
            ret_list.append({"url": url, "title": title, "pubTime": pubTime})

        return ret_list

    def get_content(self, params: dict):
        for _ in range(8):
            proxies = agent_pool(params['url'])["https"]
            text = get_text(params["url"], proxies)
            if text is None:
                continue
            break
        else:
            return None

        # resp = auto_request(url=params["url"], headers=headers, cookies=COOKIES, proxies=proxies)
        # if 400 <= resp.status_code <= 599:
        #     return None

        soup = BeautifulSoup(text, "html.parser")
        content = soup.select_one("div.articleBox")
        if content is None:
            return None
        content = handle_str.completion_url(str(content), params["url"])

        return {"title": params["title"], "pubTime": params["pubTime"], "url": params["url"], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
