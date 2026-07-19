# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

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
            # 招投标情况
            {
                "url": "https://smp.mhedu.sh.cn/zhmh/data/loadNewsList",
                "page_number": 1,
                'data': {
                    "lm": "GJWbExkR",
                    "currentPage": 1
                },
                't': 1
            },
            # 仪器医疗器械图书药品等物资采购
            {
                "url": "https://smp.mhedu.sh.cn/zhmh/data/loadNewsList",
                "page_number": 1,
                'data': {
                    "lm": "N2ChVv2i",
                    "currentPage": 1
                },
                't': 1
            },
            # 通知公告
            {
                "url": "https://smp.mhedu.sh.cn/zhmh/data/loadNewsList",
                "page_number": 1,
                'data': {
                    "lm": "FdgOf9L5",
                    "currentPage": 1
                },
                't': 2
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy(), 't': p['t']
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, json=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data').get('list')

        for row in rows:
            if params['t'] == 1:
                bak1 = row.get('bak1').split('.')[0]
                url = f"https://smp.mhedu.sh.cn/zhmh/site/mh4/newslist.html?m=bU28wz0I&pm=5lybn9C0&bak1={bak1}"
            else:
                if row.get('ljdz') and "mp.weixin.qq" in row.get('ljdz'):
                    continue

                id = row.get('id')
                url = f"https://smp.mhedu.sh.cn/zhmh/site/mh4/news.html?m={id}"

            title = row.get('bt')
            pubTime = row.get('fbsj')

            if params['t'] == 1:
                fj = row.get('fj')
                fjs = json.loads(fj)
                content = ''
                for item in fjs:
                    fj_url = f"https://smp.mhedu.sh.cn/zhmh/file/{item.get('file')}"
                    a_tag = f'<a href="{fj_url}">{item.get("title")}</a>'
                    content += a_tag
            else:
                content = row.get('nr')

            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'content': content})

        return ret_list

    def get_content(self, params: dict):
        if params.get('content'):
            return params

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.v_news_content')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
