# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str


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
                "url": "https://www.hongyuan.gov.cn/hyxrmzf/c100053/nav_list_{}.shtml",
                "page_number": 1,
            },
            # 乡镇动态
            {
                "url": "https://www.hongyuan.gov.cn/hyxrmzf/c100052/nav_list_{}.shtml",
                "page_number": 1,
            },
            # 养老服务
            {
                "url": "https://www.hongyuan.gov.cn/hyxrmzf/ylfw/nav_list_{}.shtml",
                "page_number": 1,
            },
            # 义务教育
            {
                "url": "https://www.hongyuan.gov.cn/hyxrmzf/c100098/nav_list_{}.shtml",
                "page_number": 1,
            },
            # 涉农补贴
            {
                "url": "https://www.hongyuan.gov.cn/hyxrmzf/c108593/nav_list_{}.shtml",
                "page_number": 1,
            },
            # 社会救助
            {
                "url": "https://www.hongyuan.gov.cn/hyxrmzf/c100095/nav_list_{}.shtml",
                "page_number": 1,
            },
            # 财政信息
            {
                "url": "https://www.hongyuan.gov.cn/hyxrmzf/c100093/nav_list_{}.shtml",
                "page_number": 1,
            },
            # 重大建设项目
            {
                "url": "https://www.hongyuan.gov.cn/hyxrmzf/c100094/nav_list_{}.shtml",
                "page_number": 1,
            },
            # 环境保护
            {
                "url": "https://www.hongyuan.gov.cn/hyxrmzf/c100100/nav_list_{}.shtml",
                "page_number": 1,
            },
            # 乡村振兴
            {
                "url": "https://www.hongyuan.gov.cn/hyxrmzf/c101420/nav_list_{}.shtml",
                "page_number": 1,
            },
            # 结果公开
            {
                "url": "https://www.hongyuan.gov.cn/hyxrmzf/c100107/nav_list_{}.shtml",
                "page_number": 1,
            },
            # 决策公开
            {
                "url": "https://www.hongyuan.gov.cn/hyxrmzf/c100103/nav_list_{}.shtml",
                "page_number": 1,
            },
            # 执行公开
            {
                "url": "https://www.hongyuan.gov.cn/hyxrmzf/c100104/nav_list_{}.shtml",
                "page_number": 1,
            },

        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                url = p['url'].format(index) if index > 1 else p['url'].replace('_{}', '')
                cls.start_urls.append(
                    {
                        'url': url,
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        soup = BeautifulSoup(resp.text, "html.parser")
        wrap = soup.select_one('div.nav_list_list_container > ul')
        rows = wrap.select('li') if wrap else []

        for row in rows:
            a_tag = row.select_one('a')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.get('title')
            pubTime = row.select_one('span').get_text(strip=True)
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.common_detail, div#NewsContent')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
