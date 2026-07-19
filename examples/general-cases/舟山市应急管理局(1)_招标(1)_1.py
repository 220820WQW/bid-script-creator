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
            # 公告公示
            {
                "url": "http://zsyj.zhoushan.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?webId=2746&pageId=1229333261&parseType=bulidstatic&pageType=column&tagId=%E5%BD%93%E5%89%8D%E5%AD%90%E6%A0%8F%E7%9B%AElist&tplSetId=320n0YgHTGIvJDvqCxUo2&paramJson=%7B%22pageNo%22%3A1%2C%22pageSize%22%3A%2220%22%7D",
                "page_number": 1,
            },
            # 政策法规处
            {
                "url": "http://zsyj.zhoushan.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?webId=2746&pageId=1603692&parseType=bulidstatic&pageType=column&tagId=%E5%BD%93%E5%89%8D%E5%AD%90%E6%A0%8F%E7%9B%AElist&tplSetId=320n0YgHTGIvJDvqCxUo2&paramJson=%7B%22pageNo%22%3A1%2C%22pageSize%22%3A20%7D",
                "page_number": 1,
            },

            # 国务院办公厅文件
            {
                "url": "https://www.zhoushan.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?webId=2237&pageId=1229020879&parseType=bulidstatic&pageType=column&tagId=%E5%BD%93%E5%89%8D%E6%A0%8F%E7%9B%AE%E5%88%97%E8%A1%A81a&tplSetId=uvPSpStckwuUfzDgHfE86&paramJson=%7B%22pageNo%22%3A1%2C%22pageSize%22%3A15%7D",
                "page_number": 1,
            },
            # 浙江省规章、文件
            {
                "url": "https://www.zhoushan.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?parseType=bulidstatic&webId=2237&tplSetId=uvPSpStckwuUfzDgHfE86&pageType=column&tagId=%E5%BD%93%E5%89%8D%E6%A0%8F%E7%9B%AE%E5%88%97%E8%A1%A81a&editType=null&pageId=1229020880",
                "page_number": 1,
            },
            # 重大决策公开目录
            {
                "url": "https://www.zhoushan.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?parseType=bulidstatic&webId=2237&tplSetId=uvPSpStckwuUfzDgHfE86&pageType=column&tagId=%E5%BD%93%E5%89%8D%E6%A0%8F%E7%9B%AE%E5%88%97%E8%A1%A81a&editType=null&pageId=1229294965",
                "page_number": 1,
            },
            # 征集公告（行政规范性文件）
            {
                "url": "https://www.zhoushan.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?parseType=bulidstatic&webId=2237&tplSetId=uvPSpStckwuUfzDgHfE86&pageType=column&tagId=%E5%BD%93%E5%89%8D%E6%A0%8F%E7%9B%AE%E5%88%97%E8%A1%A81a&editType=null&pageId=1229294966",
                "page_number": 1,
            },
            # 采纳情况（行政规范性文件）
            {
                "url": "https://www.zhoushan.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?parseType=bulidstatic&webId=2237&tplSetId=uvPSpStckwuUfzDgHfE86&pageType=column&tagId=%E5%BD%93%E5%89%8D%E6%A0%8F%E7%9B%AE%E5%88%97%E8%A1%A81a&editType=null&pageId=1229294967",
                "page_number": 1,
            },
            # 人大代表建议办理
            {
                "url": "https://www.zhoushan.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?parseType=bulidstatic&webId=2237&tplSetId=uvPSpStckwuUfzDgHfE86&pageType=column&tagId=%E5%BD%93%E5%89%8D%E6%A0%8F%E7%9B%AE%E5%88%97%E8%A1%A81a&editType=null&pageId=1229895725",
                "page_number": 1,
            },
            # 政协委员提案办理
            {
                "url": "https://www.zhoushan.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?parseType=bulidstatic&webId=2237&tplSetId=uvPSpStckwuUfzDgHfE86&pageType=column&tagId=%E5%BD%93%E5%89%8D%E6%A0%8F%E7%9B%AE%E5%88%97%E8%A1%A81a&editType=null&pageId=1229895726",
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
        wrap = soup.select_one('div.page-content')
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
        content = soup.select_one('div#zoom, div.contM, div#size')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
