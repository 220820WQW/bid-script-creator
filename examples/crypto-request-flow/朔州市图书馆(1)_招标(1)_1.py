# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse, urlencode

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re
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
        return hostname.lower().removeprefix("www.")

    if _is_attachment(url_a) or _is_attachment(url_b):
        return False

    domain_a = _get_domain(url_a)
    domain_b = _get_domain(url_b)
    return domain_a == domain_b


# endregion


HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "http://www.szlib.sx.cn/entry/v2/sub/df378d57504715c638a76d062ab01581",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}
COOKIES = {
    "website_id": "820134",
    "website_fid": "5978",
    "website_fid_login": "0",
    "mh_sign": "937121bf9d864ec2713180c23cab437b2d434ab145e4318c262a05f651c9d676",
    "goc": "o",
    "webIdEnc": "7421304a44062111f01beb3065d4e1546d0b",
    "current_page_id": "1794565"
}


def get_sign():
    for _ in range(5):
        url = "http://www.szlib.sx.cn/entry/v2/sub/df378d57504715c638a76d062ab01581"
        resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES)
        if resp.status_code != 200:
            continue

        e = re.search("engineId = '(.*?)';", resp.text).group(1)
        t = re.search("typeId = '(.*?)';", resp.text).group(1)

        hp = re.search("hp = '(.*?)';", resp.text).group(1)
        webPubId = re.search("webPubId = '(.*?)';", resp.text).group(1)
        aid = re.search("aid = '(.*?)';", resp.text).group(1)
        p_wfwfid = re.search("p_wfwfid = (.*?);", resp.text).group(1)
        return e, t, hp, webPubId, aid, p_wfwfid
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
            # 通知公告
            {
                "url": "http://www.szlib.sx.cn/engine2/data/api-v2/0/type/datas",
                "page_number": 1,
                'data': {
                    "e": "",
                    "t": "",
                    "ap": "4",
                    "sw": "",
                    "p2": "8",
                    "p": "1",
                    "nv": "true",
                    "m": "0"
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

        try:
            e, t, hp, webPubId, aid, p_wfwfid = get_sign()
        except:
            return ret_list

        params['data']['e'] = e
        params['data']['t'] = t

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, params=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        obj = resp.json().get('data').get('datas')
        rows = obj.get('datas')

        for row in rows:
            payload = {
                "u": f"/v2/sub/982bd8fc6b371311ed2b98463d0c7ad16b23/{e}/0/{row.get('publicId')}/{hp}/{aid}/{webPubId}/{p_wfwfid}?app=0&version=undefined",
                "p": hp
            }
            u = f"http://www.szlib.sx.cn/entry/sub-page-link/add?{urlencode(payload)}"

            resp = request.post(url=u, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                continue

            data = resp.json().get('data')
            url = f"http://www.szlib.sx.cn/entry/v2/sub/{data}"

            title = row.get('1').get('value')
            pubTime = row.get('6').get('value')

            detail_url = urljoin(params['url'], row.get('dataUrl'))
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'detailUrl': detail_url})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['detailUrl'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        obj = resp.json().get('data')
        content = obj.get('content')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
