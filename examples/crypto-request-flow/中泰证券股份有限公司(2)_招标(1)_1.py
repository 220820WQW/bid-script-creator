# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad
import time
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
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Authorization": "cd5941df3ac974544cde30f32e62116a6168bc424c0c8749b0778392dac2499292b122cd82236126",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://www.zts.com.cn/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-App-Key": "50afb4aceb38497d9e95ee6c9d3a38df",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
COOKIES = {
    "Path": "/",
    "sajssdk_2015_cross_new_user": "1",
    "sensorsdata2015jssdkcross": "%7B%22distinct_id%22%3A%2219f358051182c0e-03c03a6f1be1f0e-26011b51-2073600-19f35805119326d%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTlmMzU4MDUxMTgyYzBlLTAzYzAzYTZmMWJlMWYwZS0yNjAxMWI1MS0yMDczNjAwLTE5ZjM1ODA1MTE5MzI2ZCJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219f358051182c0e-03c03a6f1be1f0e-26011b51-2073600-19f35805119326d%22%7D",
    "sensorsdata2015jssdksession": "%7B%22session_id%22%3A%2219f36981ed8d3609d6a673e2808726011b51207360019f36981ed92897%22%2C%22first_session_time%22%3A1783327366872%2C%22latest_session_time%22%3A1783327381474%7D"
}


def build_authorization():
    key = b"947dcfd3"
    ts = str(int(time.time() * 1000))
    plain = ("enRzLW5ldC1jbGllbnQ=&" + ts).encode("utf-8")
    return DES.new(key, DES.MODE_ECB).encrypt(pad(plain, 8)).hex()


def decrypt_result(result_text):
    key = b"947dcfd3"
    data = bytes.fromhex(result_text)
    plain = unpad(DES.new(key, DES.MODE_ECB).decrypt(data), 8)
    return json.loads(plain.decode("utf-8"))


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 重要通知
            {
                "url": "https://www.zts.com.cn/clientApi/article/getArticleList?columnId=3465&title=&pageSize=10&pageNum=1&PublishTo=portal",
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

        headers = HEADERS.copy()
        headers['Authorization'] = build_authorization()

        resp = auto_request(url=params['url'], headers=headers, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('rows')

        for row in rows:
            id = row.get('id')
            url = f"https://www.zts.com.cn/news/article/detail/{id}"

            title = row.get('title')
            pubTime = row.get('publishTime')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id})

        return ret_list

    def get_content(self, params: dict):
        headers = HEADERS.copy()
        headers['Authorization'] = build_authorization()

        url = f"https://www.zts.com.cn/clientApi/article/getArticleDetail?id={params['id']}"
        resp = auto_request(url, headers=headers, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        obj = resp.json().get('data')
        content = obj.get('content')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
