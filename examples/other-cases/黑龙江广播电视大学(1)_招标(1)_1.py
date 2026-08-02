# -*- coding: UTF-8 -*-
import json
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bbSpider import Spider, request, handle_str


# region fixed methods
def auto_request(
    url, params=None, data=None, json=None, proxy_safety=None, **kwargs
):
    if proxy_safety is None:
        proxy_safety = urlparse(url).scheme

    if data is not None or json is not None:
        resp = request.post(
            url,
            params=params,
            data=data,
            json=json,
            proxy_safety=proxy_safety,
            **kwargs,
        )
    else:
        resp = request.get(
            url,
            params=params,
            proxy_safety=proxy_safety,
            **kwargs,
        )

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


def encode_parameter(text):
    return ",".join(str(ord(char)) for char in text) + ","


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
                "url": "https://www.hljrtvu.org.cn/post",
                "page_number": 1,
                "data": {
                    "sql": "select a.id,a.频道id,a.新闻标题,a.操作时间,a.新闻类型,a.是否置顶,a.新闻标题  as 显示标题 from 新闻_新闻内容信息表 a left join 新闻_新闻频道信息表 b on a.频道id=b.id where a.数据状态='已审核' and a.删除标志=0 and a.是否在主页中显示='是' and b.idstr like '%c2681c820e14fd520211028093656551%' order by a.是否置顶 Desc, a.操作时间 desc",
                    "rowAmount": 30,
                    "pageNum": 1,
                },
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                data = p['data'].copy()
                data['pageNum'] = index
                cls.start_urls.append({'url': p['url'], 'data': data})

    def get_list(self, params: dict):
        ret_list = []
        data = {
            "serviceClassName": "framework.service.QueryDataList",
            "serviceName": "queryList",
            "parameter": encode_parameter(json.dumps(params['data'], ensure_ascii=False, separators=(",", ":"))),
            "sysPara": "{}",
        }
        resp = auto_request(url=params['url'], data=data, headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        site_url = "https://www.hljrtvu.org.cn/listPage.html?pdid=c2681c820e14fd520211028093656551"
        for row in json.loads(resp.json().get('data')):
            url = f"https://www.hljrtvu.org.cn/infoPage.html?pdid={row.get('频道id')}&xwid={row.get('id')}"
            if not is_same_origin_url(url, site_url):
                continue
            ret_list.append({
                'url': url,
                'title': row.get('新闻标题').strip(),
                'pubTime': row.get('操作时间'),
                'id': row.get('id'),
            })

        return ret_list

    def get_content(self, params: dict):
        parameter = f"[{{sql:\"select a.* from 新闻_新闻内容信息表 a where a.id='{params['id']}'\"}}]"
        data = {
            "serviceClassName": "framework.service.baseDataAccessService",
            "serviceName": "queryMaps",
            "parameter": encode_parameter(parameter),
            "sysPara": "{}",
        }
        resp = auto_request(url="https://www.hljrtvu.org.cn/post", data=data, headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        row = json.loads(resp.json().get('data'))[0].get('data')[0]
        content = "".join(chr(int(code)) for code in row.get('新闻内容').split(",") if code)
        content = content.replace("218.7.19.197:8080", "218.7.19.206")
        content = content.replace("218.7.19.206", "www.hljou.org.cn")
        content = handle_str.completion_url(content, params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
