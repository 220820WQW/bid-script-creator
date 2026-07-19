# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re


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
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://www.osln.org.cn",
    "Pragma": "no-cache",
    "Referer": "https://www.osln.org.cn/tzgg",
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
    "ASP.NET_SessionId": "trdtc1dawhjfp0djpslaflxr",
    "__RequestVerificationToken": "x52GvkVfUcXWaq9B3Qg1Y2TD2F18AK13NWWZLDt8eTVfRK7FtjPGIirukUeKvubPgk5jPVoNde5Fv4i9b1N2QkNH2MzJhgq9V6PPFScd5Ko1"
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
                "url": "https://www.osln.org.cn/Designer/Common/GetData",
                "page_number": 3,
                'data': {
                    "dataType": "news",
                    "key": "",
                    "pageIndex": "0",
                    "pageSize": "7",
                    "selectCategory": "269924",
                    "selectId": "",
                    "dateFormater": "yyyy-MM-dd",
                    "orderByField": "createtime",
                    "orderByType": "desc",
                    "templateId": "0",
                    "postData": "",
                    "es": "false",
                    "setTop": "true",
                    "__RequestVerificationToken": "8mfGJcUqxdwZsGLVUMGF47DSzU_CqnfxC0LGFsCYNmRcbAX_-lfjKAdJufiByHZs0X1RXYFMjMrM2vu_nhb3N1TXWCkZAQfqqnt5H0aK3iY1"
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

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, data=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('Data')

        for row in rows:
            LinkUrl = row.get('LinkUrl')
            url = urljoin(params['url'], LinkUrl)
            if not is_same_origin_url(url, params['url']):
                continue

            title = row.get('Name')
            pubTime = row.get('QTime')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        src = soup.select_one('#smart-body > script').get('src')

        resp = auto_request(url=src, headers=HEADERS, cookies=COOKIES)
        m = re.search(r"document.write\((.*)\);", resp.text)
        text = m.group(1).replace('\\r\\n', '').replace('\\u0027', '"').replace('\\u003e', '>').replace('\\u003c', '<').replace('\\', '').replace('u0026nbsp;', '')
        soup = BeautifulSoup(text, "html.parser")

        content = soup.select_one('div.w-detailcontent')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
