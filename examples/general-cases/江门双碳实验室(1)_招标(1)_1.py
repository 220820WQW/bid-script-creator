# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str


def auto_request(url, params=None, data=None, json=None, proxy_safety=None, **kwargs):
    """
    自动区分 GET / POST
    :param url: 请求地址
    :param params: URL 查询参数
    :param data: 表单 data
    :param json: JSON 请求体
    :param proxy_safety: 代理类型: http / https
    :param kwargs: 自动接收 headers / cookies / timeout / allow_redirects / verify / proxies 等
    """
    proxy_safety = proxy_safety if proxy_safety else urlparse(url).scheme
    # 有 data 或 json 自动走 POST
    if data is not None or json is not None:
        resp = request.post(url, params=params, data=data, json=json, proxy_safety=proxy_safety, **kwargs)
    # 无请求体 走 GET
    else:
        resp = request.get(url, params=params, proxy_safety=proxy_safety, **kwargs)

    resp.encoding = resp.apparent_encoding
    return resp


def is_same_origin_url(url_a: str, url_b: str):
    """判断两个URL是否同源（仅对比域名，忽略www和大小写）"""
    # 定义附件后缀
    suffix = {".pdf", ".doc", ".docx", ".xls", ".xlsx"}

    # 检查是否为附件
    def _is_attachment(url: str) -> bool:
        path = urlparse(url).path.lower()
        return path.endswith(tuple(suffix))

    if _is_attachment(url_a) or _is_attachment(url_b):
        return False

    # 同源域名判断
    domain_a = urlparse(url_a).netloc.lower().removeprefix('www.')
    domain_b = urlparse(url_b).netloc.lower().removeprefix('www.')
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
            # 工作动态
            {
                "url": "https://hkustgz-jcl.ac.cn/api",
                "page_number": 1,
                'data': {
                    "m": "impact",
                    "a": "get_news_list",
                    "p": "1",
                    "type": "2"
                }
            },
            # 科研进展
            {
                "url": "https://hkustgz-jcl.ac.cn/api",
                "page_number": 1,
                'data': {
                    "m": "impact",
                    "a": "get_news_list",
                    "p": "1",
                    "ps": "10",
                    "time": "",
                    "type": "0"
                }
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy()
                    }
                )

    def get_list(self, params: dict):
        """
        :param params: start_urls中的每一项数据;
        :return: 包含内容的url等; e.g.[{'url': 'xx', 'title': 'xx', 'pubTime': 'xx',...}]
        """
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, data=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        obj = resp.json()
        rows = obj.get('news_list')

        for row in rows:
            id = row.get('id')
            url = f"https://hkustgz-jcl.ac.cn/publicationsDetail?id={id}&tabName=Events"

            title = row.get('cn_title')
            pubTime = row.get('news_time')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id})

        return ret_list

    def get_content(self, params: dict):
        """
        :param params: get_list中返回的每一项数据;
        :return: 由title, pubTime, url, content等key构建的dict数据类型;
        """
        url = "https://hkustgz-jcl.ac.cn/api"
        payload = {
            "m": "impact",
            "a": "get_news_info",
            "id": params['id']
        }
        resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES, data=payload)
        if 400 <= resp.status_code <= 599:
            return None

        obj = resp.json().get('news_info')
        content = obj.get('cn_content')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
