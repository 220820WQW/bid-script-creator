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


HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://www.linfenkx.com/tzgg",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
COOKIES = {
    "ASP.NET_SessionId": "25ihbcwxkkepxdssn2tstw15",
    "__RequestVerificationToken": "_LhJ_77xxBfK_A9bVXhxCMsly_WuN3ZGiUb6POyjB5C8aLEL0wvL3tXQvalFulJF2DyENotgC7bOtyUV4f2eDGRXV05iDPc5DjC1B8ic7FY1"
}


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
                "url": "https://img.wanwang.xin/pubsf/10199/10199697/cdn-static-pages/pages/pc/1677_zh-cn.html.Body.js?version=20260610125757",
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

        resp = request.get(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        m = re.search(r"document.write\((.*)\);", resp.text)
        text = m.group(1).replace('\\r\\n', '').replace('\\u0027', '"').replace('\\u003e', '>').replace('\\u003c', '<').replace('\\', '')
        soup = BeautifulSoup(text, "html.parser")
        wrap = soup.select_one('ul#ulList_con_10_41')
        rows = wrap.select('li') if wrap else []

        for row in rows:
            a_tag = row.select_one('a')
            url = urljoin("https://www.linfenkx.com/tzgg", a_tag.get('href'))

            title = a_tag.get_text(strip=True)
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
        src = soup.select_one('#smart-body > script').get('src')

        resp = auto_request(url=src, headers=HEADERS, cookies=COOKIES)
        m = re.search(r"document.write\((.*)\);", resp.text)
        text = m.group(1).replace('\\r\\n', '').replace('\\u0027', '"').replace('\\u003e', '>').replace('\\u003c', '<').replace('\\', '')
        soup = BeautifulSoup(text, "html.parser")

        content = soup.select_one('div.trs_editor_view, div.Section0, div.w-detailcontent')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
