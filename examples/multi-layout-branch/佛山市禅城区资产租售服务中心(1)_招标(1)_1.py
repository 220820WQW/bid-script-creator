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
            # 交易公告
            {
                "url": "https://wy.chancheng.gov.cn/api/wz/getNoticeListByTypeId.form?pageNum={}&pageSize=10&typeId=newsType_0040001&keyWord=",
                "page_number": 2,
                't': 1
            },
            # 结果公示
            {
                "url": "https://wy.chancheng.gov.cn/api/wz/getNoticeListByTypeId.form?pageNum={}&pageSize=10&typeId=fec97a34-e161-4bf0-b23a-9fc2af652c69&keyWord=",
                "page_number": 2,
                't': 1
            },

            # 标的
            {
                "url": "https://wy.chancheng.gov.cn/api/wz/getBidList.form?wytype=&area=&status=&term=0&pageNum={}&pageSize=12&keyword=&bidName=",
                "page_number": 20,
                't': 2
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                if p['t'] == 1:
                    cls.start_urls.append(
                        {
                            'url': p['url'].format(index - 1), 't': p['t']
                        }
                    )
                else:
                    cls.start_urls.append(
                        {
                            'url': p['url'].format(index), 't': p['t']
                        }
                    )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, data={})
        if 400 <= resp.status_code <= 599:
            return ret_list

        if params['t'] == 1:
            rows = resp.json().get('body').get('resultList')

            for row in rows:
                id = row.get('id')
                url = f"https://wy.chancheng.gov.cn/index.html#/news-detail?id={id}"

                title = row.get('title')
                pubTime = row.get('publishDate')

                content = row.get('content')
                content = handle_str.completion_url(str(content), params['url'])
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'content': content})
        if params['t'] == 2:
            rows = resp.json().get('body').get('data')

            for row in rows:
                id = row.get('id')
                url = f"https://wy.chancheng.gov.cn/index.html#/index-scene-detail?id={id}"

                title = row.get('title')
                pubTime = row.get('biddingtime')

                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id})

        return ret_list

    def get_content(self, params: dict):
        if params.get('content'):
            return params

        url = f"https://wy.chancheng.gov.cn/api/wz/getBidInfo.form?id={params['id']}"
        resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES, data={})
        if 400 <= resp.status_code <= 599:
            return None

        bidinfo = resp.json().get('body')
        content = ""

        if description := bidinfo.get('description'):
            content += description

        if announcement := bidinfo.get('announcement'):
            content += announcement

        if attContractList := bidinfo.get('attContractList'):
            for attach in attContractList:
                a_tag = f'<a href="{attach.get("url")}">{attach.get("name")}</a>'
                content += a_tag

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
