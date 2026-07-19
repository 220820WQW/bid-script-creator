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
            # 公示公告
            {
                "url": "http://www.weibin.gov.cn/col5196/col5202/",
                "page_number": 1,
                "t": 1
            },
            # 建议提案
            {
                "url": "http://www.weibin.gov.cn/col15477/col15480/col15490/",
                "page_number": 1,
                "t": 2
            },
            # 规划计划
            {
                "url": "http://www.weibin.gov.cn/col15477/col15480/col15491/",
                "page_number": 1,
                "t": 2
            },
            # 招标投标
            {
                "url": "http://www.weibin.gov.cn/col15477/col15480/col15492/",
                "page_number": 1,
                "t": 2
            },
            # 养老服务
            {
                "url": "http://www.weibin.gov.cn/col15477/col15480/col15501/col15530/",
                "page_number": 1,
                "t": 2
            },
            # 交通运输
            {
                "url": "http://www.weibin.gov.cn/col15477/col15480/col15501/col18233/",
                "page_number": 1,
                "t": 2
            },
            # 征地拆迁信息
            {
                "url": "http://www.weibin.gov.cn/col15477/col15480/col15507/col15544/",
                "page_number": 1,
                "t": 2
            },
            # 乡村振兴
            {
                "url": "http://www.weibin.gov.cn/col15477/col15480/col15558/",
                "page_number": 1,
                "t": 2
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
            rows = soup.select('.xx_list li')

            for row in rows:
                a_tag = row.select_one('a[href]')
                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                title = a_tag.get('title') or a_tag.get_text(strip=True)
                pubTime = row.select_one('span').get_text(strip=True)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        if params['t'] == 2:
            rows = soup.select('div.default_pgContainer li')

            for row in rows:
                a_tag = row.select_one('a[href]')
                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                title = a_tag.get('title') or a_tag.get_text(strip=True)
                pubTime = row.select_one('b').get_text(strip=True)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('#Zoom .trs_editor_view') or soup.select_one('.trs_editor_view') or soup.select_one('#Zoom')

        annex_box = soup.select_one('#Zoom .public-annex-downLoad')
        if annex_box:
            for a_tag in annex_box.select('a[href]'):
                href = urljoin(params['url'], a_tag.get('href'))
                if href.lower().endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx')):
                    content.append(soup.new_tag('br'))
                    content.append(soup.new_tag('a', href=href, string=a_tag.get_text(strip=True)))

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
