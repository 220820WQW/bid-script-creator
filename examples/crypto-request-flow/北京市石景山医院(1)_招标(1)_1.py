# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import json


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
AES_KEY = b"IRCo4Jf0suh9MvEf"


def encrypt_request_data(data):
    text = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    encrypted = AES.new(AES_KEY, AES.MODE_ECB).encrypt(pad(text, AES.block_size))
    return base64.b64encode(encrypted).decode('utf-8')


def decrypt_response_data(data):
    text = AES.new(AES_KEY, AES.MODE_ECB).decrypt(base64.b64decode(data))
    return json.loads(unpad(text, AES.block_size).decode('utf-8'))


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
                "url": "https://www.bjsjsyy.com.cn/prod-api/system/notice/list",
                "page_number": 1,
                "data": {
                    "pageSize": 10,
                    "pageNum": 1,
                    "subjectKey": "sys_notice_news",
                },
            },
            # 招标公开
            {
                "url": "https://www.bjsjsyy.com.cn/prod-api/system/notice/list",
                "page_number": 1,
                "data": {
                    "pageSize": 10,
                    "pageNum": 1,
                    "subjectKey": "sys_zhaobiao_enws",
                },
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                data = p['data'].copy()
                data['pageNum'] = index
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': data,
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        data = {"data": encrypt_request_data(params['data'])}
        resp = auto_request(url=params['url'], json=data, headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = decrypt_response_data(resp.json()).get('data').get('list')
        from_name = '通知公告' if params['data']['subjectKey'] == 'sys_notice_news' else '招标公开'
        for row in rows:
            notice_id = row.get('noticeId')
            url = f"https://www.bjsjsyy.com.cn/#/publicInfo/newsDetail?id={notice_id}&from={from_name}"
            url = urljoin('https://www.bjsjsyy.com.cn/#/publicInfo/notice', url)
            if not is_same_origin_url(url, 'https://www.bjsjsyy.com.cn/#/publicInfo/notice'):
                continue

            title = handle_str.replace_escape(row.get('noticeTitle')).strip()
            pubTime = row.get('createTime')
            ret_list.append(
                {'url': url, 'title': title, 'pubTime': pubTime, 'noticeId': notice_id}
            )

        return ret_list

    def get_content(self, params: dict):
        data = {"noticeId": str(params['noticeId'])}
        body = {"data": encrypt_request_data(data)}
        resp = auto_request(
            url="https://www.bjsjsyy.com.cn/prod-api/system/notice/getNoticeInfo",
            json=body,
            headers=HEADERS,
            cookies=COOKIES,
        )
        if 400 <= resp.status_code <= 599:
            return None

        obj = decrypt_response_data(resp.json()).get('data')
        content = obj.get('noticeContent')
        content = handle_str.completion_url(str(content), params['url'])

        return {
            "title": params['title'],
            "pubTime": params['pubTime'],
            "url": params['url'],
            "content": content,
        }


if __name__ == "__main__":
    CrawlerObject().start()
