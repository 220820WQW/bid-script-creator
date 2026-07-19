# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
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


HEADERS = {}
COOKIES = {}

KEY = b"abcdefgabcdefg12"
IV = b"abcdefgabcdefg12"


def encrypt_str(bean):
    raw = json.dumps(bean, ensure_ascii=False, separators=(",", ":"))
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    return base64.b64encode(cipher.encrypt(pad(raw.encode("utf-8"), 16))).decode("utf-8")


def decrypt_text(text):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    plain = unpad(cipher.decrypt(base64.b64decode(text.strip())), 16)
    return plain.decode("utf-8")


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
                "url": "https://iacq.com.cn/CQIA/restservices/api/EncryService/query",
                "page_number": 1,
                'data': {
                    "shortname": "cqia_tzgg",
                    "pagesize": 12,
                    "pagenum": 1
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

        body = {"method": "getNewContentsweb", "str": encrypt_str(params['data'])}
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, json=body)
        if 400 <= resp.status_code <= 599:
            return ret_list

        plain = decrypt_text(resp.text)
        data = json.loads(plain)
        rows = data.get('result').get('result')

        for row in rows:
            id = row.get('id')
            prename = row.get('prename')
            catlevel = row.get('catlevel')
            url = f"https://iacq.com.cn/CQIA/LEAP/IAWEB/index.html#/CQIAWEB/newsInfo?name={prename}&secondmenu=cqia_tzgg&catlevel={catlevel}&newsid={id}"

            title = row.get('title')
            pubTime = row.get('createtime')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, "id": id})

        return ret_list

    def get_content(self, params: dict):
        bean = {"id": params['id'], "pagesize": "1", "pagenum": "1"}
        body = {"method": "getNewContentsweb", "str": encrypt_str(bean)}

        resp = auto_request(url="https://iacq.com.cn/CQIA/restservices/api/EncryService/query", headers=HEADERS, cookies=COOKIES, json=body)
        if 400 <= resp.status_code <= 599:
            return None

        plain = decrypt_text(resp.text)
        data = json.loads(plain)

        content = data.get('result').get('result')[0].get('content')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
