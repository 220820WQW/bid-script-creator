# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bbSpider import Spider, request, handle_str
import execjs
from bbSpider.utils import acquire_subjoin_path


# region fixed methods
def auto_request(
    url, params=None, data=None, json=None, proxy_safety=None, **kwargs
):
    if proxy_safety is None:
        proxy_safety = urlparse(url).scheme

    if data is not None or json is not None:
        resp = request.post(
            url,
            params=params,
            data=data,
            json=json,
            proxy_safety=proxy_safety,
            **kwargs,
        )
    else:
        resp = request.get(
            url,
            params=params,
            proxy_safety=proxy_safety,
            **kwargs,
        )

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



def get_cookies():
    for _ in range(8):
        headers = {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8,"
                "application/signed-exchange;v=b3;q=0.7"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/132.0.0.0 Safari/537.36"
            ),
        }

        url = "https://www.jinniu.gov.cn/jinniu/c180283/xmzc.shtml"
        response = request.get(url, headers=headers, verify=False)
        cookies = response.cookies.get_dict()

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.select_one("meta[id][content]").get("content")
        code = soup.select_one("script").text

        src = soup.select_one("head script[src]").get("src")
        domain_url = urljoin(url, src)
        resp = request.get(domain_url, headers=headers)
        if resp.status_code != 200:
            continue

        domain = resp.text

        path = acquire_subjoin_path("金牛区人民政府1.js")
        with open(path, "rt", encoding="utf-8") as file:
            js_code = file.read()

        output = execjs.compile(js_code).call(
            "general_cookie", content, code, domain
        )
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
            # 项目招采
            {
                "url": "https://api.chengdu.gov.cn/cdhbjkV2/index.php/Weather/aqimap",
                "page_number": 1,
                "data": {
                    "x-msc-token": "zy2fPoFoFv4B9K67vDt4LBpoFp0N9DRn",
                    "search": 1,
                    "websiteId": "6ab0f1326e88429d99ada2dbb08f7d63",
                    "channelId": "ba102d27aa13432abe9f3f18d6d5a7cf",
                    "domainMetaList[0][platname]": "",
                    "domainMetaList[1][type]": "",
                    "title": "",
                    "pageNum": 1,
                    "pageSize": 15,
                },
            },
            # 资产招租
            {
                "url": "https://api.chengdu.gov.cn/cdhbjkV2/index.php/Weather/aqimap",
                "page_number": 1,
                "data": {
                    "x-msc-token": "zy2fPoFoFv4B9K67vDt4LBpoFp0N9DRn",
                    "search": 1,
                    "websiteId": "6ab0f1326e88429d99ada2dbb08f7d63",
                    "channelId": "8e467e537b4b4622baa6eafc547ccac4",
                    "domainMetaList[0][platname]": "",
                    "domainMetaList[1][type]": "",
                    "title": "",
                    "pageNum": 1,
                    "pageSize": 15,
                },
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                data = p['data'].copy()
                data['pageNum'] = index
                cls.start_urls.append({'url': p['url'], 'data': data})

    def get_list(self, params: dict):
        ret_list = []

        cookies = get_cookies()
        if cookies is None:
            return ret_list

        resp = auto_request(
            url=params['url'],
            params=params['data'],
            headers=HEADERS,
            cookies=cookies,
        )
        if 400 <= resp.status_code <= 599:
            return ret_list

        site_url = "https://www.jinniu.gov.cn"
        for row in resp.json().get('results'):
            url = urljoin(site_url, row.get('url'))
            if not is_same_origin_url(url, site_url):
                continue

            ret_list.append({
                'url': url,
                'title': row.get('title'),
                'pubTime': row.get('publishedTime'),
            })

        return ret_list

    def get_content(self, params: dict):
        cookies = get_cookies()
        if cookies is None:
            return None

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=cookies)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.details_text')
        content = handle_str.completion_url(str(content), params['url'])

        return {
            "title": params['title'],
            "pubTime": params['pubTime'],
            "url": params['url'],
            "content": content,
        }


if __name__ == "__main__":
    CrawlerObject().start()
