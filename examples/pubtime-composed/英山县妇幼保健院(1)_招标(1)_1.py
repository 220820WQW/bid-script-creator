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
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://www.ysxfybjy.cn",
    "Pragma": "no-cache",
    "Referer": "https://www.ysxfybjy.cn/h-col-129.html",
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
    "_siteStatId": "d3ae5348-ae05-4f2e-98b1-2f7557acbad6",
    "_siteStatDay": "20260624",
    "_siteStatVisitorType": "visitorType_31003895",
    "_siteStatRedirectUv": "redirectUv_31003895",
    "_siteStatVisit": "visit_31003895",
    "_cliid": "zcvh87K4fCzuH8s7",
    "_checkSiteLvBrowser": "true",
    "_reqArgs": "",
    "_siteStatReVisit": "reVisit_31003895",
    "_siteStatVisitTime": "1782266933389"
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
            # 通知公告
            {
                "url": "https://www.ysxfybjy.cn/ajax/ajaxLoadModuleDom_h.jsp",
                "page_number": 1,
                'data': {
                    "cmd": "getWafNotCk_getAjaxPageModuleInfo",
                    "_colId": "129",
                    "_extId": "0",
                    "moduleId": "2216",
                    "href": "/col.jsp?m2216pageno=1&id=129",
                    "newNextPage": "false",
                    "needIncToVue": "false"
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

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, data=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        domStr = resp.json().get('domStr')
        soup = BeautifulSoup(domStr, "html.parser")
        rows = soup.select('div.m_news_list > div.m_news_content')

        for row in rows:
            a_tag = row.select_one('.news_title a')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.select_one('.title_content').get_text(strip=True)
            year = row.select_one('.big_time').get_text(strip=True)
            day = row.select_one('.small_time').get_text(strip=True)
            pubTime = f"{year}-{day}"
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.richContent')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
