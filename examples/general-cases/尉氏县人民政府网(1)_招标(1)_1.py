# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import json


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
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "http://www.wschina.gov.cn",
    "Pragma": "no-cache",
    "Referer": "http://www.wschina.gov.cn/kfswsxwz/tzggx/pc/list.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}
COOKIES = {
    "__jsluid_h": "cfa78028ca4082831d88102ac019c490",
    "yfx_c_g_u_id_10000044": "_ck26070814385113737567123523870",
    "yfx_f_l_v_t_10000044": "f_t_1783492731357__r_t_1783492731357__v_t_1783492731357__r_c_0",
    "arialoadData": "false",
    "ariaappid": "83ecc432191f796bf0036f6f222fc6f9",
    "ariauseGraymode": "false"
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
            # 通知公告 打开超慢
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "tzggx"
                }
            },
            # 政府采购
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "c00476"
                }
            },
            # 规划信息
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "c00458"
                }
            },
            # 决策预公开
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "c00483"
                }
            },
            # 建议提案办理
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "c00484"
                }
            },
            # 养老服务
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "c00885"
                }
            },
            # 涉农补贴
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "c00961"
                }
            },
            # 义务教育
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "c00965"
                }
            },
            # 自然资源
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "c00973"
                }
            },
            # 交通运输
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "c00985"
                }
            },
            # 水利
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "c01001"
                }
            },
            # 城乡规划
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "c00500"
                }
            },
            # 征地补偿
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "c00501"
                }
            },
            # 国有土地房屋征收
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "c00507"
                }
            },
            # 扶贫
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "c00513"
                }
            },
            # 重大建设项目
            {
                "url": "http://www.wschina.gov.cn/queryList",
                "page_number": 1,
                'data': {
                    "current": "1",
                    "pageSize": "15",
                    "webSiteCode[]": "kfswsxwz",
                    "channelCode[]": "c00146"
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
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, data=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data').get('results')

        for row in rows:
            urls_raw = row.get('source').get('urls')
            urls = json.loads(urls_raw).get('pc')
            url = urljoin(params['url'], urls)
            if not is_same_origin_url(url, params['url']):
                continue

            title = row.get('source').get('title')
            pubTime = row.get('source').get('pubDate')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.article-content')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
