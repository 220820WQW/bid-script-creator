# -*- coding: UTF-8 -*-
import base64
import json
from datetime import datetime
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str


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
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "http://szzyjy.com.cn",
    "Pragma": "no-cache",
    "Referer": "http://szzyjy.com.cn/jyxx/tradeInfo.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}
COOKIES = {}


def get_cookies():
    for _ in range(8):
        url = "http://szzyjy.com.cn/EpointWebBuilder/frontAppAction.action?cmd=addPageView"
        payload = {"viewGuid": "cms_003", "siteGuid": "7eb5f7f1-9041-43ad-8e13-8fcb82ea831a"}
        resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES, data=payload)
        if 400 <= resp.status_code <= 599:
            continue

        return resp.cookies.get_dict()
    else:
        return None


def get_captcha_code(cookies):
    for _ in range(8):
        url = "http://szzyjy.com.cn/EpointWebBuilder/frontAppAction.action?cmd=getVerificationCode"
        payload = {"width": "100", "height": "40", "codeNum": "4", "interferenceLine": "1", "codeGuid": ""}
        resp = auto_request(url=url, headers=HEADERS, cookies=cookies, data=payload)
        if 400 <= resp.status_code <= 599:
            continue

        data = json.loads(resp.json().get('custom'))
        img_guid = data.get('verificationCodeGuid')
        yzm_raw = data.get('verificationCodeValue')
        yzm = base64.b64decode(yzm_raw).decode('utf-8')
        return img_guid, yzm
    else:
        return None


def get_last_month():
    now = datetime.now()
    year = now.year
    month = now.month

    if month == 1:
        last_month_year = year - 1
        last_month_month = 12
    else:
        last_month_year = year
        last_month_month = month - 1

    last_month = datetime(last_month_year, last_month_month, now.day)
    last_month_time = last_month.strftime('%Y-%m-%d')
    return last_month_time


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 交易信息
            {
                "url": "http://szzyjy.com.cn/EpointWebBuilder/JyxxSearchAction.action",
                "page_number": 15,
                'data': {
                    "cmd": "getList1",
                    "categorynum": "003",
                    "diqu": "苏州市",
                    "xmmc": "",
                    "zstype": "",
                    "zblx": "",
                    "starttime": "2026-05-29",
                    "endtime": "2026-06-29",
                    "siteguid": "7eb5f7f1-9041-43ad-8e13-8fcb82ea831a",
                    "pageIndex": "9",
                    "pageSize": "15"
                }
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                p['data']['pageIndex'] = str(index - 1)
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy()
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        now = datetime.now()
        now_time = now.strftime('%Y-%m-%d')
        params['data']['starttime'] = get_last_month()
        params['data']['endtime'] = now_time

        if int(params['data']['pageIndex']) <= 9:
            resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, params=params['data'])
        else:
            cookies = get_cookies()
            v = get_captcha_code(cookies)
            if v is None:
                return ret_list

            img_guid, yzm = v
            params['data']['YZM'] = yzm
            params['data']['ImgGuid'] = img_guid
            resp = auto_request(url=params['url'], headers=HEADERS, cookies=cookies, params=params['data'])

        if 400 <= resp.status_code <= 599:
            return ret_list

        obj = json.loads(resp.json().get('custom'))
        rows = obj.get('Table')

        for row in rows:
            title = row.get('title1')
            pubTime = row.get('postdate')

            categorynum = row.get('categorynum')
            infoid = row.get('infoid')
            url = f"http://szzyjy.com.cn/jump.html?infoguid={infoid}&categorynum={categorynum}"

            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, "infoid": infoid, "categorynum": categorynum})

        return ret_list

    def get_content(self, params: dict):
        url = f"http://szzyjy.com.cn/EpointWebBuilder/JyxxSearchAction.action?cmd=getDetailPath&categorynum={params['categorynum']}&infoid={params['infoid']}&siteguid=7eb5f7f1-9041-43ad-8e13-8fcb82ea831a&pageIndex=0"
        resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        url_section = resp.json().get('custom')
        url2 = urljoin('http://szzyjy.com.cn/', url_section)
        resp = auto_request(url=url2, headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.con')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
