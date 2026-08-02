# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re
import time


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
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": "http://qpq.jsnc.gov.cn",
    "Pragma": "no-cache",
    "Referer": "http://qpq.jsnc.gov.cn/newiframe/ie8/preAnnouncement.html?id=1&unid=4028858d4ff037030150173d2a756f05&allPath=1|4028858d493affb301494f4ee6500a51|4028858d4ff037030150173d2a756f05|",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}
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
                "url": "http://www.jsnc.gov.cn/cqjy-web//notice/noticeInfo",
                "page_number": 2,
                'data': {
                    "from": "2",
                    "proChildType": "",
                    "areaId": "4028858d4ff037030150173d2a756f05",
                    "unitId": "4028858d4ff037030150173d2a756f05",
                    "allPath": "1|4028858d493affb301494f4ee6500a51|4028858d4ff037030150173d2a756f05|",
                    "jymjStart": "",
                    "jymjEnd": "",
                    "bmEnd": "",
                    "cjDateStart": "",
                    "cjDateEnd": "",
                    "bmStart": "",
                    "proTypeId": "",
                    "proTypeParentId": "",
                    "xmStatus": "0",
                    "keyWords": "",
                    "order": "",
                    "orderType": "",
                    "cpage": 1,
                    "total": 109,
                    "totalpage": 7,
                    "pageSize": 16,
                    "typeChildren": [],
                    "unitList": [],
                    "childrenList": []
                }
            },
            # 成交公告
            {
                "url": "http://www.jsnc.gov.cn/cqjy-web//notice/noticeInfo",
                "page_number": 2,
                'data': {
                    "from": "3",
                    "proChildType": "",
                    "areaId": "4028858d4ff037030150173d2a756f05",
                    "status": "",
                    "unitId": "4028858d4ff037030150173d2a756f05",
                    "areaLow": "",
                    "areaUp": "",
                    "dealBegin": "",
                    "orderBy": "",
                    "dealEnd": "",
                    "turnoverStart": "",
                    "proTypeId": "",
                    "proTypeParentId": "",
                    "turnoverEnd": "",
                    "xmStatus": "5",
                    "keyWords": "",
                    "order": "",
                    "orderType": "",
                    "cpage": 2,
                    "total": 4270,
                    "totalpage": 267,
                    "pageSize": 16,
                    "typeChildren": [],
                    "unitList": [],
                    "childrenList": [],
                    "allPath": "1|4028858d493affb301494f4ee6500a51|4028858d4ff037030150173d2a756f05|"
                }
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                p['data']['cpage'] = index
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy()
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, json=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data').get('list')

        for row in rows:
            proId = row.get('proId')
            url = f"http://qpq.jsnc.gov.cn/ggxx/index.html?detailsID={proId}"

            title = row.get('proName')
            pubTime = row.get('regDate')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        # resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        # if 400 <= resp.status_code <= 599:
        #     return None

        for _ in range(8):
            try:
                content1 = request.render_page(url=params['url'], sleep_time=3000)
                if content1:
                    break
            except:
                time.sleep(1)
                continue
        else:
            return None

        soup = BeautifulSoup(content1, "html.parser")
        src = soup.select_one('.contain2').select_one('iframe').get('src')
        url = urljoin(params['url'], src)

        for _ in range(8):
            try:
                content2 = request.render_page(url, sleep_time=3000)
                if content2:
                    break
            except:
                time.sleep(1)
                continue
        else:
            return None

        soup = BeautifulSoup(content2, "html.parser")
        content = soup.select_one('.property-transaction > .main')

        # 替换所有的div链接
        if divs := content.select('div[onclick]'):
            for div in divs:
                if onclick := div.get('onclick'):
                    m = re.search(r"openFile\('(.*?)'\)", onclick)
                    if m:
                        new_a = soup.new_tag('a', href=m.group(1), string=div.get_text(strip=True))
                        new_a['style'] = div.get('style')
                        div.replace_with(new_a)

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
