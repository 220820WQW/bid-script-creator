# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re


# region fixed methods
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


HEADERS = {}
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
            # 通知公告
            {
                "url": "http://www.funing.gov.cn/col/col6617/index.html",
                "page_number": 1,
            },
            # 规范性文件
            {
                "url": "http://www.funing.gov.cn/col/col34074/index.html",
                "page_number": 1,
            },
            # 政府实事项目
            {
                "url": "http://www.funing.gov.cn/col/col31939/index.html",
                "page_number": 1,
            },
            # 涉农补贴
            {
                "url": "http://www.funing.gov.cn/col/col31941/index.html",
                "page_number": 1,
            },
            # 乡村振兴
            {
                "url": "http://www.funing.gov.cn/col/col32587/index.html",
                "page_number": 1,
            },
            # 征收和产权交易
            {
                "url": "http://www.funing.gov.cn/col/col31947/index.html",
                "page_number": 1,
            },
            # 住房保障
            {
                "url": "http://www.funing.gov.cn/col/col31948/index.html",
                "page_number": 1,
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'],
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        m = re.search(r'<datastore>(.*?)</datastore>', resp.text, re.S)
        script = m.group(1).replace('<![CDATA[', '').replace(']]>', '')

        soup = BeautifulSoup(script, "html.parser")
        rows = soup.select('li')

        for row in rows:
            a_tag = row.select_one('a')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = handle_str.replace_escape(a_tag.get('title') or a_tag.get_text(strip=True)).strip()
            if title.endswith('...'):
                title = None
            pubTime = handle_str.extract_and_validate_dates(row.get_text(strip=True))[0]
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('#zoom')

        if params['title'] is None:
            params['title'] = soup.select_one('.con-title').get_text(strip=True)
            params['title'] = handle_str.replace_escape(params['title']).strip()

        if attach := soup.select_one('div.xz'):
            content.append(attach)

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
