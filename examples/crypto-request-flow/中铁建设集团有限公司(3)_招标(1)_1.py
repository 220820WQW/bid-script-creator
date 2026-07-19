# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re
from bbSpider.agent_pool import agent_pool


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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
}

COOKIES = {
    # "safeline_bot_token": "AKtTNQYAAAAAAAAAAAAAAACxRFYinwEAAGmqQ4ScH1urmgkBEyM9UE7yfNDz"
}


def solve_cookie(proxies):
    for _ in range(8):
        response = request.get(
            "http://ztjs.crcc.cn/api-gateway/jpaas-publish-server/front/page/build/unit?webId=26&pageId=2256&parseType=bulidstatic&pageType=column&tagId=%E5%8F%B3%E4%BE%A7%E5%86%85%E5%AE%B9&tplSetId=qrKjI724Brc5dyGkKSEAd&paramJson=%7B%22pageNo%22%3A1%2C%22pageSize%22%3A15%7D",
            headers=HEADERS,
            timeout=20,
            proxies=proxies
        )
        if 400 <= response.status_code <= 599:
            continue

        challenge = re.search(r"safeline_bot_challenge=([^;]+)", response.headers.get("set-cookie", "")).group(1)
        prefix = re.search(r"var prefix = '([^']+)';//arg1", response.text).group(1)
        bits = int(re.search(r"var leading_zero_bit = (\d+);", response.text).group(1))

        suffix = None
        for i in range(200000):
            candidate = format(i, "x")
            digest = __import__("hashlib").sha1((prefix + candidate).encode()).hexdigest()
            binary = bin(int(digest, 16))[2:].zfill(160)
            if binary.startswith("0" * bits):
                suffix = candidate
                break

        return f"safeline_bot_challenge={challenge}; safeline_bot_challenge_ans={challenge}{suffix}"

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
            # 集团新闻
            {
                "url": "http://ztjs.crcc.cn/api-gateway/jpaas-publish-server/front/page/build/unit",
                "page_number": 1,
                'data': {
                    "webId": "26",
                    "pageId": "2256",
                    "parseType": "bulidstatic",
                    "pageType": "column",
                    "tagId": "右侧内容",
                    "tplSetId": "qrKjI724Brc5dyGkKSEAd",
                    "paramJson": "{\"pageNo\":1,\"pageSize\":\"15\"}"
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

        proxies = agent_pool(params['url'])[urlparse(params['url']).scheme]
        cookie = solve_cookie(proxies)
        if cookie is None:
            return ret_list

        resp = auto_request(url=params['url'], headers={**HEADERS, "Cookie": cookie}, params=params['data'], proxies=proxies)
        if 400 <= resp.status_code <= 599:
            return ret_list

        html = resp.json().get('data').get('html')
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select('div.page-content li')

        for row in rows:
            a_tag = row.select_one('a')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.select_one('.title').get_text(strip=True)
            pubTime = row.select_one('.time').get_text(strip=True)
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        proxies = agent_pool(params['url'])[urlparse(params['url']).scheme]
        cookie = solve_cookie(proxies)
        if cookie is None:
            return None

        resp = auto_request(url=params['url'], headers={**HEADERS, "Cookie": cookie}, proxies=proxies)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div#zoomFont')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
