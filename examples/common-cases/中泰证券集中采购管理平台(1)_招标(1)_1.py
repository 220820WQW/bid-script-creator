# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

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
    "Content-Type": "application/json; charset=UTF-8",
    "Origin": "https://ztjzcg.zts.com.cn",
    "Pragma": "no-cache",
    "Referer": "https://ztjzcg.zts.com.cn/cms/default/webfile/tender-qb/index.html",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
COOKIES = {
    "sajssdk_2015_cross_new_user": "1",
    "sensorsdata2015jssdkcross": "%7B%22distinct_id%22%3A%2219f358051182c0e-03c03a6f1be1f0e-26011b51-2073600-19f35805119326d%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTlmMzU4MDUxMTgyYzBlLTAzYzAzYTZmMWJlMWYwZS0yNjAxMWI1MS0yMDczNjAwLTE5ZjM1ODA1MTE5MzI2ZCJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219f358051182c0e-03c03a6f1be1f0e-26011b51-2073600-19f35805119326d%22%7D",
    "sensorsdata2015jssdksession": "%7B%22session_id%22%3A%2219f3580512222d804ae6815e9aa74c26011b51207360019f3580512335d4%22%2C%22first_session_time%22%3A1783309029666%2C%22latest_session_time%22%3A1783309155939%7D"
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
            # 招标信息
            {
                "url": "https://ztjzcg.zts.com.cn/cms/api/dynamicData/queryContentPage",
                "page_number": 5,
                'data': {
                    "pageNo": 2,
                    "pageSize": "10",
                    "dto": {
                        "siteId": "725",
                        "categoryId": "1105207985711349760,1105208330009182208,1105208693697282048,1105208871175061504,1105209116365684736",
                        "city": "",
                        "county": "",
                        "purchaseMode": "",
                        "secondCompanyId": "",
                        "title": ""
                    }
                }
            },
            # 非招标信息
            {
                "url": "https://ztjzcg.zts.com.cn/cms/api/dynamicData/queryContentPage",
                "page_number": 5,
                'data': {
                    "pageSize": "10",
                    "dto": {
                        "siteId": "725",
                        "categoryId": "1105209923047784448,1105210174882185216,1105210334727110656,1105210687384190976,1105210861045153792",
                        "city": "",
                        "county": "",
                        "purchaseMode": "",
                        "secondCompanyId": "",
                        "title": ""
                    }
                }
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                p['data']['pageNo'] = index
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

        obj = resp.json().get('res')
        rows = obj.get('rows')

        for row in rows:
            u = row.get('url')
            url = f"https://ztjzcg.zts.com.cn/cms/default/webfile{u}"

            title = row.get('title')
            pubTime = row.get('publishDate')
            pubTime = handle_str.extract_and_validate_dates(pubTime)[0]
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.text-part-text')

        if a := content.select_one('.table-mock'):
            a.decompose()

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
