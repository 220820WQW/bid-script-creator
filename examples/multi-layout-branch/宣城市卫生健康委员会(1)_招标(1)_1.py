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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
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
            # 通知公告
            {
                "url": "https://wjw.xuancheng.gov.cn/News/showList/3361/page_1.html",
                "page_number": 1,
                "t": 1,
            },
            # 重大行政决策预公开
            {
                "url": "https://wjw.xuancheng.gov.cn/XxgkContent/showList/174/105276/page_1.html",
                "page_number": 1,
                "t": 2,
            },
            # 人大代表建议办理
            {
                "url": "https://wjw.xuancheng.gov.cn/XxgkContent/showList/174/103128/page_1.html",
                "page_number": 1,
                "t": 3,
            },
            # 监督保障
            {
                "url": "https://wjw.xuancheng.gov.cn/XxgkContent/showList/174/103134/page_1.html",
                "page_number": 1,
                "t": 2,
            },
            # "双随机、一公开"
            {
                "url": "https://wjw.xuancheng.gov.cn/XxgkContent/showList/174/191349/page_1.html",
                "page_number": 1,
                "t": 3,
            },
            # 招标采购
            {
                "url": "https://wjw.xuancheng.gov.cn/XxgkContent/showList/174/103123/page_1.html",
                "page_number": 1,
                "t": 2,
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'], 't': p['t']
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        soup = BeautifulSoup(resp.text, "html.parser")

        if params['t'] == 1:
            rows = soup.select('div.listright-box > ul > li')

            for row in rows:
                a_tag = row.select_one('a')
                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                title = a_tag.get('title') or a_tag.get_text(strip=True)
                pubTime = row.select_one('span').get_text(strip=True)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 't': params['t']})

        if params['t'] == 2:
            rows = soup.select('section.m-tglist ul li')

            for row in rows:
                a_tag = row.select_one('a')
                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                title = a_tag.get('title') or a_tag.get_text(strip=True)
                pubTime = row.select_one('span').get_text(strip=True)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 't': params['t']})

        if params['t'] == 3:
            rows = soup.select('div.search-list tbody tr')

            for row in rows:
                a_tag = row.select_one('td.bt a')
                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                title = a_tag.get_text(strip=True)
                pubTime = row.select_one('td.cwrq').get_text(strip=True)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 't': params['t']})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        if params['t'] == 1:
            content = soup.select_one('div.newscontnet .text')
        else:
            content = soup.select_one('div.g-detailbox')

            if fj_tag := soup.select_one('.m-file-download'):
                content.append(fj_tag)

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
