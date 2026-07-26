# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import execjs
from bbSpider.utils import acquire_subjoin_path


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
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://sz.tobacco.gov.cn",
    "Pragma": "no-cache",
    "Referer": "https://sz.tobacco.gov.cn/web/szyc/zdy/zfxxgk_gggs.html",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
COOKIES = {}


def get_cookies():
    for _ in range(3):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        }

        url = "https://sz.tobacco.gov.cn/web/"
        response = request.get(url, headers=headers, verify=False, proxy_safety="https")

        cookies = response.cookies.get_dict()

        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.select_one('meta[id][content]').get('content')

        code = soup.select_one('script').text

        tag = soup.select_one('head script[src]')
        domain_url = urljoin(url, tag.get('src'))
        resp = request.get(domain_url, headers=headers, proxy_safety="https")
        if 400 <= resp.status_code <= 599:
            continue

        domain = resp.text

        with open(acquire_subjoin_path('深圳市烟草专卖局1.js'), 'rt', encoding='utf-8') as f:
            js_code = f.read()

        output = execjs.compile(js_code).call('general_cookie', content, code, domain)

        cookies.update(output)
        if len(cookies) < 2:
            continue

        return cookies
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
                "url": "https://sz.tobacco.gov.cn/web/szyc/comm",
                "page_number": 1,
                'data': {
                    "crupage": 1,
                    "pageSize": 15,
                    "s": "",
                    "tb": "wz_wenzhang",
                    "category": "%E9%80%9A%E7%9F%A5%E5%85%AC%E5%91%8A",
                    "numconfiug": "gggs"
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

        cookies = get_cookies()
        if cookies is None:
            return ret_list

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=cookies, json=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data').get('records')

        for row in rows:
            url = urljoin(params['url'], row.get('url'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = row.get('TITLE')
            pubTime = row.get('FABUDATETIME')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        cookies = get_cookies()
        if cookies is None:
            return None

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=cookies)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.subject')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
