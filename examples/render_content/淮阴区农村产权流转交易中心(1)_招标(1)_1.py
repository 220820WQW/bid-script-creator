# -*- coding: UTF-8 -*-
import re
import time
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bbSpider import Spider, request, handle_str


# region fixed public func
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
    "Content-Type": "application/json",
    "Origin": "http://hyq.jsnc.gov.cn",
    "Referer": "http://hyq.jsnc.gov.cn/",
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
            # 预公告
            {
                "url": "http://www.jsnc.gov.cn/cqjy-web//notice/noticeInfo",
                "page_number": 1,
                "t": 1,
                "data": {
                    "from": "1",
                    "unitId": "4028858d4ff03703015017fb995671cd",
                    "allPath": "1%7C4028858d493affb301494f4ee6500a51%7C4028858d4ff03703015017fb995671cd%7C",
                    "proTypeId": "",
                    "proTypeParentId": "",
                    "xmStatus": "0",
                    "cjDateStart": "",
                    "cjDateEnd": "",
                    "bmStart": "",
                    "bmEnd": "",
                    "jymjStart": "",
                    "jymjEnd": "",
                    "keyWords": "",
                    "order": "",
                    "orderType": "",
                    "cpage": 1,
                    "pageSize": 16,
                },
            },
            # 通知公告
            {
                "url": "http://www.jsnc.gov.cn/cqjy-web//notice/noticeInfo",
                "page_number": 2,
                "t": 2,
                "data": {
                    "from": "2",
                    "unitId": "4028858d4ff03703015017fb995671cd",
                    "allPath": "1%7C4028858d493affb301494f4ee6500a51%7C4028858d4ff03703015017fb995671cd%7C",
                    "proTypeId": "",
                    "proTypeParentId": "",
                    "xmStatus": "0",
                    "cjDateStart": "",
                    "cjDateEnd": "",
                    "bmStart": "",
                    "bmEnd": "",
                    "jymjStart": "",
                    "jymjEnd": "",
                    "keyWords": "",
                    "order": "",
                    "orderType": "",
                    "cpage": 1,
                    "pageSize": 16,
                },
            },
            # 成交公告
            {
                "url": "http://www.jsnc.gov.cn/cqjy-web//notice/noticeInfo",
                "page_number": 3,
                "t": 3,
                "data": {
                    "from": "3",
                    "unitId": "4028858d4ff03703015017fb995671cd",
                    "allPath": "1%7C4028858d493affb301494f4ee6500a51%7C4028858d4ff03703015017fb995671cd%7C",
                    "proTypeId": "",
                    "proTypeParentId": "",
                    "xmStatus": "5",
                    "cjDateStart": "",
                    "cjDateEnd": "",
                    "bmStart": "",
                    "bmEnd": "",
                    "jymjStart": "",
                    "jymjEnd": "",
                    "keyWords": "",
                    "order": "",
                    "orderType": "",
                    "cpage": 1,
                    "pageSize": 16,
                },
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                data = p['data'].copy()
                data['cpage'] = index
                cls.start_urls.append({'url': p['url'], 'data': data, 't': p['t']})

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], json=params['data'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data').get('list')
        for row in rows:
            if params['t'] == 1:
                detail_type = 'view-advance'
                pubTime = row.get('regDate')
            elif params['t'] == 2:
                detail_type = 'view-notice'
                pubTime = row.get('intoTime').split()[0]
            else:
                detail_type = 'view-deal'
                pubTime = row.get('turnoverTime')

            url = f"http://hyq.jsnc.gov.cn/ggxx/index.html?detailsID={row.get('proId')}&state={row.get('xmStatus')}&type={detail_type}&unid=4028858d4ff03703015017fb995671cd"
            if not is_same_origin_url(url, "http://hyq.jsnc.gov.cn"):
                continue

            ret_list.append({'url': url, 'title': row.get('proName').strip(), 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        for _ in range(8):
            try:
                content1 = request.render_page(url=params['url'], sleep_time=3000)
                if content1:
                    break
            except Exception:
                time.sleep(1)
        else:
            return None

        soup = BeautifulSoup(content1, "html.parser")
        url = urljoin(params['url'], soup.select_one('.contain2 iframe').get('src'))

        for _ in range(8):
            try:
                content2 = request.render_page(url=url, sleep_time=3000)
                if content2:
                    break
            except Exception:
                time.sleep(1)
        else:
            return None

        soup = BeautifulSoup(content2, "html.parser")
        content = soup.select_one('.property-transaction > .main')
        for div in content.select('div[onclick]'):
            match = re.search(r"openFile\('(.*?)'\)", div.get('onclick'))
            if match:
                a_tag = soup.new_tag('a', href=match.group(1), string=div.get_text(strip=True))
                a_tag['style'] = div.get('style')
                div.replace_with(a_tag)

        content = handle_str.completion_url(str(content), url)
        return {
            "title": params['title'],
            "pubTime": params['pubTime'],
            "url": params['url'],
            "content": content,
        }


if __name__ == "__main__":
    CrawlerObject().start()
