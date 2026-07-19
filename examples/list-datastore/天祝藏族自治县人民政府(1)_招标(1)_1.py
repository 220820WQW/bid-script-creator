# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re


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
            # 国务院和国务院办公厅文件
            {
                "url": "https://www.gstianzhu.gov.cn/col/col3582/index.html",
                "page_number": 1,
            },
            # 市政府和市政府办公室文件
            {
                "url": "https://www.gstianzhu.gov.cn/col/col3584/index.html",
                "page_number": 1,
            },

            # 空间规划
            {
                "url": "https://www.gstianzhu.gov.cn/col/col30593/index.html",
                "page_number": 1,
            },
            # 配套政策文件
            {
                "url": "https://www.gstianzhu.gov.cn/col/col3707/index.html",
                "page_number": 1,
            },

            # 行政许可
            {
                "url": "https://www.gstianzhu.gov.cn/col/col3675/index.html",
                "page_number": 1,
            },

            # 县属国有企业招标采购公告公示栏
            {
                "url": "https://www.gstianzhu.gov.cn/col/col31816/index.html",
                "page_number": 1,
            },

            # 养老机构
            {
                "url": "https://www.gstianzhu.gov.cn/col/col3740/index.html",
                "page_number": 1,
            },
            # 办事服务
            {
                "url": "https://www.gstianzhu.gov.cn/col/col3741/index.html",
                "page_number": 1,
            },
            # 政策法规
            {
                "url": "https://www.gstianzhu.gov.cn/col/col3743/index.html",
                "page_number": 1,
            },

            # 重大决策预公开
            {
                "url": "https://www.gstianzhu.gov.cn/col/col3797/index.html",
                "page_number": 1,
            },
            # 重大项目建设
            {
                "url": "https://www.gstianzhu.gov.cn/col/col28428/index.html",
                "page_number": 1,
            },
            # 养老服务信息公开目录
            {
                "url": "https://www.gstianzhu.gov.cn/col/col28406/index.html",
                "page_number": 1,
            },
            # 生态环境质量
            {
                "url": "https://www.gstianzhu.gov.cn/col/col3885/index.html",
                "page_number": 1,
            },
            # 重大建设项目环境管理
            {
                "url": "https://www.gstianzhu.gov.cn/col/col3886/index.html",
                "page_number": 1,
            },
            # 决策草案意见反馈
            {
                "url": "https://www.gstianzhu.gov.cn/col/col30288/index.html",
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

        m = re.search(r'<datastore>(.*?)</datastore>', resp.text, re.S)
        script = m.group(1).replace('<![CDATA[', '').replace(']]>', '')

        soup = BeautifulSoup(script, "html.parser")
        rows = soup.select('li')

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
        """
        :param params: get_list中返回的每一项数据;
        :return: 由title, pubTime, url, content等key构建的dict数据类型;
        """
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div#Zoom')

        if pdf_iframe := content.select_one('iframe'):
            pdf_tag = soup.new_tag('a', href=pdf_iframe.get('src'), string="附件")
            content.append(pdf_tag)
            pdf_iframe.decompose()

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
