# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re
import json
import html

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
                "url": "https://www.caexpo.org.cn/b2bshop/api/themeRos/public/posts/searchByVariables?page=0&size=6&filter=status+eq+%27PUBLISHED%27+and+type+eq+%27ANNOUNCEMENT%27+and+language+eq+%27ZH_CN%27",
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

        obj = resp.json().get('arrayData').get('0').get('_embedded')
        rows = obj.get('b2b:posts')

        for row in rows:
            url = row.get('url')
            if not is_same_origin_url(url, params['url']):
                continue

            title = row.get('title')
            pubTime = row.get('publishTime')
            pubTime = handle_str.extract_and_validate_dates(pubTime)[0]
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        m = re.search(r'"content":"(.*?)",', resp.text, re.S)
        content_raw = m.group(1)
        content_json_text = json.loads('"' + content_raw + '"')
        content_obj = json.loads(content_json_text)
        content = content_obj.get('html')

        m2 = re.search(r'"publicAttachments":(.*?),"source"', resp.text, re.S)
        if m2:
            attachments = json.loads(m2.group(1))
            for item in attachments:
                a_tag = f'<a =href="{item.get("attachment").get("showUrl")}">{item.get("attachment").get("name")}</a>'
                content += a_tag

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
