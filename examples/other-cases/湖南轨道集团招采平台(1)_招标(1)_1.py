# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bbSpider import Spider, request, handle_str
import hashlib
import json
import time


# region fixed public func
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


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 中标公告
            {
                "url": "https://hnrt.kdcloud.com/kapi/app/srm/srmwebapi",
                "page_number": 1,
                "data": {
                    "page": 1,
                    "size": 20,
                    "type": "5,A,B,bidproject",
                    "apiname": "getPortalNoticeData",
                    "methodname": "getPortalNoticeData",
                    "accountId": "1549127685240838144",
                },
            },
            # 招标公告
            {
                "url": "https://hnrt.kdcloud.com/kapi/app/srm/srmwebapi",
                "page_number": 1,
                "data": {
                    "page": 1,
                    "size": 20,
                    "type": "1,2,3,4,C,bidproject",
                    "componentid": "1484094329416073216",
                    "apiname": "getPortalNoticeData",
                    "methodname": "getPortalNoticeData",
                    "accountId": "1549127685240838144",
                },
            },
            # 流标公告
            {
                "url": "https://hnrt.kdcloud.com/kapi/app/srm/srmwebapi",
                "page_number": 1,
                "data": {
                    "page": 1,
                    "size": 20,
                    "type": "D",
                    "componentid": "1484095900191309824",
                    "apiname": "getPortalNoticeData",
                    "methodname": "getPortalNoticeData",
                    "accountId": "1549127685240838144",
                },
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                data = p['data'].copy()
                data['page'] = index
                cls.start_urls.append({'url': p['url'], 'data': data})

    def get_list(self, params: dict):
        ret_list = []
        resp = auto_request(
            url=params['url'],
            params=params['data'],
            headers={"accountid": params['data']['accountId']},
        )
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data').get('noticedata')
        for row in rows:
            url = row.get('url')
            if not is_same_origin_url(url, params['url']):
                continue

            ret_list.append({
                'url': url,
                'title': row.get('noticename'),
                'pubTime': row.get('publishtime'),
                'noticeId': row.get('noticeId'),
                'mobileurl': row.get('mobileurl'),
            })

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['mobileurl'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        cookies = resp.cookies.get_dict()
        headers = {
            "ajax": "true",
            "cqappid": "bos",
            "kdcdc": "1549127685240838144",
            "userid": "1549127685240838144_-1",
        }
        resp = auto_request(
            url="https://hnrt.kdcloud.com/form/getConfig.do",
            params={
                "params": json.dumps({
                    "formId": "mobsp_quonotice_view",
                    "accountId": "1549127685240838144",
                    "billid": params['noticeId'],
                    "userId": "guest",
                    "flag": "test",
                    "f": "test",
                }, separators=(',', ':')),
            },
            headers=headers,
            cookies=cookies,
        )
        if 400 <= resp.status_code <= 599:
            return None

        cookies.update(resp.cookies.get_dict())
        page_id = resp.json().get('pageId')
        csrf_token = resp.headers.get('kd-csrf-token')
        request_params = '[{"key":"","methodName":"loadData","args":[],"postData":[]}]'
        start_time = str(int(time.time() * 1000))
        headers.update({
            "cqappid": "mobsp",
            "kd-csrf-token": csrf_token,
            "client-start-time": start_time,
            "signature": hashlib.sha256(
                (start_time + csrf_token + "0" + request_params).encode()
            ).hexdigest() + f"0__length__{len(request_params)}",
        })
        resp = auto_request(
            url="https://hnrt.kdcloud.com/form/batchInvokeAction.do?appId=mobsp&f=mobsp_quonotice_view&ac=loadData",
            data={"pageId": page_id, "appId": "mobsp", "params": request_params},
            headers=headers,
            cookies=cookies,
        )
        if 400 <= resp.status_code <= 599:
            return None

        data = {item.get('k'): item.get('v', item.get('data')) for item in resp.json()[0].get('p')}
        content = handle_str.completion_url(data.get('htmlap'), params['url'])
        return {
            "title": params['title'],
            "pubTime": params['pubTime'],
            "url": params['url'],
            "content": content,
        }


if __name__ == "__main__":
    CrawlerObject().start()
