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
    "Origin": "http://www.zjszyyy.cn",
    "Pragma": "no-cache",
    "Referer": "http://www.zjszyyy.cn/col.jsp?id=123",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}
COOKIES = {
    "_siteStatId": "24619294-ac04-4aef-a5c6-506326b33456",
    "_siteStatDay": "20260624",
    "_siteStatVisitorType": "visitorType_7873547",
    "_siteStatRedirectUv": "redirectUv_7873547",
    "_siteStatVisit": "visit_7873547",
    "_cliid": "DQuAA0JgwJDYMOQ2",
    "www.zjszyyy.cn__VSIGN_485": "AIvp7dEGCgQ3MTg3ENSJmscB",
    "SECKEY_ABVK": "fU3LUkAOD61+3JF5EUj0TFnafKcH8w9qOBR/WvGV96w%3D",
    "BMAP_SECKEY": "H6lrGkgubnEqHFDTxUgQ0_g1S0VMEkg3C_oMNr_kSU7c-90MM0MvnQRLrfkWHpUzEpca6GvGtBx47qeXlIku2mwQcMkTYd_U5XaW7hFjsMmH-fIDL2pkcMxriRvUQT9FH2sUDZ0Wfn_gAIBqyr117Oevo69wxOFLcOpGqjSJbNBoybEDGS1kTWD9DuETysb6",
    "_checkSiteLvBrowser": "true",
    "_siteStatReVisit": "reVisit_7873547",
    "_reqArgs": "",
    "_lastEnterDay": "2026-06-24",
    "_siteStatVisitTime": "1782281575327"
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
            # 院内新闻
            {
                "url": "http://www.zjszyyy.cn/ajax/ajaxLoadModuleDom_h.jsp",
                "page_number": 1,
                'data': {
                    "cmd": "getWafNotCk_getAjaxPageModuleInfo",
                    "_colId": "123",
                    "_extId": "0",
                    "moduleId": "562",
                    "href": "/col.jsp?m562pageno=1&id=123",
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

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, data=params['data'], proxy_safety='https')
        if 400 <= resp.status_code <= 599:
            return ret_list

        domStr = resp.json().get('domStr')
        soup = BeautifulSoup(domStr, "html.parser")
        rows = soup.select('div#newsList562 table.J_lineBody')

        for row in rows:
            a_tag = row.select_one('a.J_mixNewsStyleTitle')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.get_text(strip=True)
            pubTime = row.select_one('span.mixNewsStyleDate').get_text(strip=True)
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, proxy_safety='https')
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.richContent')

        if iframes := content.select('iframe'):
            for iframe in iframes:
                src = iframe.get('src').split("=")[-1]
                url = f'http://7873547.s21i.faiusr.com/61/{src}'
                a_tag = soup.new_tag('a', href=url, string="内容附件")
                content.append(a_tag)
                iframe.decompose()

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
