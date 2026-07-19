# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re
import json

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
            # 通知公告
            {
                "url": "http://ccpithz.huzhou.gov.cn/xwdt/tzgg/index.html",
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
        """
        :param params: start_urls中的每一项数据;
        :return: 包含内容的url等; e.g.[{'url': 'xx', 'title': 'xx', 'pubTime': 'xx',...}]
        """
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        m = re.search(r'var dataList=(.*);.*?var pagesData', resp.text)
        rows = json.loads(m.group(1))

        for row in rows:
            for i in row.get('infolist'):
                url = i.get('url')
                if not is_same_origin_url(url, params['url']):
                    continue

                title = i.get('title')
                pubTime = i.get('daytime')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        """
        :param params: get_list中返回的每一项数据;
        :return: 由title, pubTime, url, content等key构建的dict数据类型;
        """
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('td#zoom')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
