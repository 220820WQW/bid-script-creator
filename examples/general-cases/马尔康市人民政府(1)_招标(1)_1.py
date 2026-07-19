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
            # 规划计划
            {
                "url": "http://maerkang.gov.cn/maerkang/c100086/nav_list.shtml",
                "page_number": 1,
            },
            # 招标采购
            {
                "url": "http://maerkang.gov.cn/maerkang/c102144/nav_list.shtml",
                "page_number": 1,
            },
            # 政策文件
            {
                "url": "http://maerkang.gov.cn/maerkang/c106289/nav_list.shtml",
                "page_number": 1,
            },
            # 自然资源
            {
                "url": "http://maerkang.gov.cn/maerkang/zrzy/nav_list.shtml",
                "page_number": 1,
            },
            # 养老服务
            {
                "url": "http://maerkang.gov.cn/maerkang/c102136/nav_list.shtml",
                "page_number": 1,
            },
            # 义务教育
            {
                "url": "http://maerkang.gov.cn/maerkang/c100098/nav_list.shtml",
                "page_number": 1,
            },
            # 涉农补贴
            {
                "url": "http://maerkang.gov.cn/maerkang/c108584/nav_list.shtml",
                "page_number": 1,
            },
            # 社会救助
            {
                "url": "http://maerkang.gov.cn/maerkang/shjz/nav_list.shtml",
                "page_number": 1,
            },
            # 重大项目建设
            {
                "url": "http://maerkang.gov.cn/maerkang/c100094/nav_list.shtml",
                "page_number": 1,
            },
            # 环境保护
            {
                "url": "http://maerkang.gov.cn/maerkang/c100100/nav_list.shtml",
                "page_number": 1,
            },
            # 乡村振兴
            {
                "url": "http://maerkang.gov.cn/maerkang/c102138/nav_list.shtml",
                "page_number": 1,
            },
            # 助企纾困
            {
                "url": "http://maerkang.gov.cn/maerkang/zqsk/nav_list.shtml",
                "page_number": 1,
            },
            # 决策公开
            {
                "url": "http://maerkang.gov.cn/maerkang/c100103/nav_list.shtml",
                "page_number": 1,
            },
            # 管理公开
            {
                "url": "http://maerkang.gov.cn/maerkang/c100105/nav_list.shtml",
                "page_number": 1,
            },
            # 服务公开
            {
                "url": "http://maerkang.gov.cn/maerkang/c100106/nav_list.shtml",
                "page_number": 1,
            },
            # 结果公开
            {
                "url": "http://maerkang.gov.cn/maerkang/c100107/nav_list.shtml",
                "page_number": 1,
            },
            # 通知公告
            {
                "url": "http://www.maerkang.gov.cn/maerkang/c100053/nav_list.shtml",
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

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select('div.nav_list_list_container ul li')

        for row in rows:
            a_tag = row.select_one('a')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.select_one('p').get_text(strip=True)
            pubTime = row.select_one('span').get_text(strip=True)
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.common_detail')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
