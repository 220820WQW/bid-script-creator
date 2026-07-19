# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import hashlib
import random
import time


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
    # "accessToken": "mEg6hzrKQblhIlV3iPwTv",
    # "nonce": "FoV7ZnBexOHsu5cZJHAPYN9SSGjKt7yu",
    # "sign": "D59C35B319779203C79CBEC923AB17BE",
    # "timestamp": "1783411627879"
}
COOKIES = {
    "JSESSIONID": "38A3D9F026372F8E92B569356C6E8564"
}


def js_str(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def make_nonce():
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    return "".join(chars[int(61 * random.random())] for _ in range(32))


def md5_upper(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest().upper()


def build_sign(headers, params=None, data=None, method="get"):
    params = params or {}
    data = data or {}
    if method.lower() == "post":
        data = {k: v for k, v in data.items() if v or v == 0}

    merged = {}
    merged.update(headers)
    merged.update(data)
    merged.update(params)
    merged.pop("isRepeat", None)

    keys = sorted(headers) if method.lower() == "put" else sorted(merged)
    raw = "&".join(
        f"{k}={js_str(merged[k])}"
        for k in keys
        if merged.get(k) is not None
    )
    return md5_upper(raw), raw


def get_access_token():
    for _ in range(8):
        resp = auto_request(
            "http://fjbwy.com/api/token",
            params={
                "appid": "62f2152576287ea87a728701",
                "appsecret": "780eec1f481e9217a9d339b17f8c107f33bba22e949acf8911843bb59d52eee7",
            },
            timeout=20,
        )
        if 400 <= resp.status_code <= 599:
            continue

        access_token = resp.json()["data"]["accessToken"]
        return access_token
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
            # 采购信息
            {
                "url": "http://fjbwy.com/api/cms/app/usually/article",
                "page_number": 1,
                "data": {
                    "page.current": "1",
                    "page.size": "10",
                    "isShowSummary": "true",
                    "isShowChild": "true",
                    "categoryCode": "cgxx"
                }
            },
            # 信息公开
            {
                "url": "http://fjbwy.com/api/cms/app/usually/article",
                "page_number": 1,
                'data': {
                    "page.current": "1",
                    "page.size": "10",
                    "isShowSummary": "true",
                    "isShowChild": "true",
                    "categoryCode": "xxgk"
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

        access_token = get_access_token()
        if access_token is None:
            return ret_list

        headers = {
            "nonce": make_nonce(),
            "timestamp": str(int(time.time() * 1000)),
            "accessToken": access_token,
        }

        sign, raw = build_sign(headers, params=params['data'], method="get")
        headers["sign"] = sign

        resp = auto_request(url=params['url'], headers=headers, cookies=COOKIES, params=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data').get('records')

        for row in rows:
            id = row.get('id')
            url = f"http://fjbwy.com/home/news/detail?id={id}&code={params['data']['categoryCode']}"

            title = row.get('title')
            pubTime = row.get('finalPublishDate')
            pubTime = handle_str.time_stamp(int(pubTime))
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id})

        return ret_list

    def get_content(self, params: dict):
        access_token = get_access_token()
        if access_token is None:
            return None

        headers = {
            "nonce": make_nonce(),
            "timestamp": str(int(time.time() * 1000)),
            "accessToken": access_token,
        }

        sign, raw = build_sign(headers, params=None, method="get")
        headers["sign"] = sign

        url = f"http://fjbwy.com/api/cms/app/usually/article/{params['id']}"
        resp = auto_request(url=url, headers=headers, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        data = resp.json().get('data')
        content = data.get('content') or data.get('title')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
