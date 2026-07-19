# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse, quote

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
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
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "http://60.190.198.7:9191",
    "Pragma": "no-cache",
    "Referer": "http://60.190.198.7:9191/ierp/isv/kingdee/pur/srmmainpage/srmmainpage.html?userId=guest&accountId=1044397164828034048",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "accountId": "1044397164828034048"
}
COOKIES = {
    "KERPSESSIONIDhailiang": "XBNXoKyyzt5rdOqF0g5tr9ubHkLL3sIGxXz2cb0XJCqUcnBikuvwdYxnxaErYrjzQ41EoAufuYwu3b28n4hBNrahgODLRAt70a5Lk7ueJuGPTlzo6q2ldylDIuXDfHMs",
    "KERPSESSIONID": "XBNXoKyyzt5rdOqF0g5tr9ubHkLL3sIGxXz2cb0XJCqUcnBikuvwdYxnxaErYrjzQ41EoAufuYwu3b28n4hBNrahgODLRAt70a5Lk7ueJuGPTlzo6q2ldylDIuXDfHMs"
}


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 招标中心/结果公告
            {
                "url": "http://60.190.198.7:9191/ierp/kapi/app/srm/srmwebapi",
                "page_number": 1,
                "data": {
                    "apiname": "srmmainpage",
                    "methodname": "getMainPageConfig",
                    "accountId": "1044397164828034048"
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

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, json=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        data = resp.json().get('data')
        obj = json.loads(data)
        categoryInfo1 = obj.get('categoryInfoShow').get('categoryInfo1')[0].get('info')
        categoryInfo2 = obj.get('resultShow').get('info')
        categoryInfo1.extend(categoryInfo2)
        rows = categoryInfo1

        url_map = {
            "招标公告": "http://60.190.198.7:9191/ierp/index.html?formId=ten_announcement_detail&noticeId={}",
            "中标结果公告": "http://60.190.198.7:9191/ierp/index.html?formId=bid_announcement_preview&noticeId={}"
        }

        for row in rows:
            url = url_map[row.get('type')].format(row.get('noticeId'))

            title = row.get('noticeName')
            pubTime = row.get('publish_time')
            ret_list.append(
                {'url': url, 'title': title, 'pubTime': pubTime, 't': row.get('type'), "noticeId": row.get('noticeId'), "cookies": resp.cookies.get_dict()}
            )

        return ret_list

    def get_content(self, params: dict):
        u1 = "http://60.190.198.7:9191/ierp/form/getConfig.do"
        payload1 = {
            "params": json.dumps({"formId": "ten_announcement_detail", "noticeId": params['noticeId']}, separators=(',', ':')),
            "random": "0.052841926271610884"
        }
        resp = auto_request(url=u1, headers=HEADERS, cookies=params['cookies'], params=payload1)
        if 400 <= resp.status_code <= 599:
            return None

        pageId = resp.json().get('pageId')
        u2 = "http://60.190.198.7:9191/ierp/form/batchInvokeAction.do?appId=ten&f=ten_announcement_detail&ac=loadData"
        payload2 = {
            "pageId": pageId,
            "appId": "ten",
            "params": "[{\"key\":\"\",\"methodName\":\"loadData\",\"args\":[],\"postData\":[]}]"
        }
        resp = request.post(url=u2, headers={}, cookies=params['cookies'], data=payload2)
        if 400 <= resp.status_code <= 599:
            return None

        if params['t'] == "招标公告":
            obj = resp.json()[2].get('p')[0]
        else:
            obj = resp.json()[1].get('p')[0]
        content = obj.get('v')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
