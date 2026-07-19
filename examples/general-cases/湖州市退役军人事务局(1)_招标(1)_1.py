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
        return hostname.lower().removeprefix("www.")

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
                "url": "http://tyjrswj.huzhou.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?webId=3651&pageId=1229512852&parseType=bulidstatic&pageType=column&tagId=%E7%BB%84%E9%85%8D%E5%88%86%E7%B1%BBlist&tplSetId=AJrs5qHpO95lyAYqV3oZT&paramJson=%7B%22pageNo%22%3A1%2C%22pageSize%22%3A15%2C%22search%22%3A%22%7B%5C%22xxgkId%5C%22%3A%5C%22OO001%5C%22%2C%5C%22xxgkType%5C%22%3A%5C%22xxgk_combination%5C%22%2C%5C%22nodeId%5C%22%3A%5C%2211330500MB1911463X%5C%22%2C%5C%22className%5C%22%3A%5C%22%5C%22%7D%22%7D",
                "page_number": 1,
            },
            # 监督保障
            {
                "url": "http://tyjrswj.huzhou.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?webId=3651&pageId=1229512852&parseType=bulidstatic&pageType=column&tagId=%E7%BB%84%E9%85%8D%E5%88%86%E7%B1%BBlist&tplSetId=AJrs5qHpO95lyAYqV3oZT&paramJson=%7B%22pageNo%22%3A1%2C%22pageSize%22%3A15%2C%22search%22%3A%22%7B%5C%22xxgkId%5C%22%3A%5C%22BB001%5C%22%2C%5C%22xxgkType%5C%22%3A%5C%22xxgk_combination%5C%22%2C%5C%22nodeId%5C%22%3A%5C%2211330500MB1911463X%5C%22%2C%5C%22className%5C%22%3A%5C%22%5C%22%7D%22%7D",
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

        html = resp.json().get('data').get('html')
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select('ul.ajax-ul li')

        for row in rows:
            a_tag = row.select_one('a')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.get_text(strip=True)
            pubTime = row.select_one('.fr').get_text(strip=True)
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.zhengw')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
