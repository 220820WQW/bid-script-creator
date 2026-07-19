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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://cggl.zssy.com.cn:8091",
    "Pragma": "no-cache",
    "Referer": "https://cggl.zssy.com.cn:8091/cgzb/portal/newCgxxList",
    "Sec-Fetch-Dest": "iframe",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
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
            # 采购公告
            {
                "url": "https://cggl.zssy.com.cn:8091/cgzb/portal/newCgxxList",
                "page_number": 10,
                'data': {
                    "pageNo": "1",
                    "pageSize": "10",
                    "querykeys": ""
                },
            },
            # 结果公告
            {
                "url": "https://cggl.zssy.com.cn:8091/cgzb/portal/newGsxxList",
                "page_number": 5,
                'data': {
                    "pageNo": "1",
                    "pageSize": "10",
                    "querykeys": ""
                }
            },
            # 调研论证公告公告
            {
                "url": "https://cggl.zssy.com.cn:8091/cgzb/portal/newCgxxList?typeId=1",
                "page_number": 1,
                'data': {}
            },
            # 需求调查公告
            {
                "url": "https://cggl.zssy.com.cn:8091/cgzb/portal/newCgxxList?typeId=2",
                "page_number": 2,
                'data': {}
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                p['data']['pageNo'] = str(index)
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy()
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        if params.get('data'):
            resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, data=params['data'])
        else:
            resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)

        if 400 <= resp.status_code <= 599:
            return ret_list

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select('table#treeTable tr')

        for row in rows:
            a_tag = row.select_one('a')
            url = urljoin(params['url'], a_tag.get('href').strip())
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.get_text(strip=True)
            pubTime = a_tag.parent.find_next_sibling('td').get_text(strip=True)
            pubTime = handle_str.extract_and_validate_dates(pubTime)[0]
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.container > .con')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
