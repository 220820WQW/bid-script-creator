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
    "Content-Type": "application/json",
    "Origin": "http://lys.jsnc.gov.cn",
    "Referer": "http://lys.jsnc.gov.cn/newiframe/ie8/preAnnouncement.html?id=1&unid=4028858b582cc56a01588a1cd18d75ea&allPath=1|4028858d48bb69370148bb6a7bdb0002|4028858b582cc56a01588a1cd18d75ea|",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
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
                "page_number": 3,
                "t": 1,
                "data": {
                    "from": "2",
                    "proChildType": "",
                    "areaId": "4028858b582cc56a01588a1cd18d75ea",
                    "unitId": "4028858b582cc56a01588a1cd18d75ea",
                    "allPath": "1|4028858d48bb69370148bb6a7bdb0002|4028858b582cc56a01588a1cd18d75ea|",
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
                    "total": 0,
                    "totalpage": 0,
                    "pageSize": 16,
                    "typeChildren": [],
                    "unitList": [],
                    "childrenList": []
                }
            },
            # 成交公告
            {
                "url": "http://www.jsnc.gov.cn/cqjy-web//notice/noticeInfo",
                "page_number": 3,
                "t": 2,
                "data": {
                    "from": "3",
                    "proChildType": "",
                    "areaId": "4028858b582cc56a01588a1cd18d75ea",
                    "status": "",
                    "unitId": "4028858b582cc56a01588a1cd18d75ea",
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
                    "cpage": 1,
                    "total": 0,
                    "totalpage": 0,
                    "pageSize": 16,
                    "typeChildren": [],
                    "unitList": [],
                    "childrenList": [],
                    "allPath": "1|4028858d48bb69370148bb6a7bdb0002|4028858b582cc56a01588a1cd18d75ea|"
                }
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                data = p['data'].copy()
                data['cpage'] = index
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': data, 't': p['t']
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, json=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data').get('list')

        for row in rows:
            pro_id = row.get('proId')
            state = row.get('xmStatus')
            url = f"http://lys.jsnc.gov.cn/ggxx/index.html?detailsID={pro_id}&state={state}"
            if not is_same_origin_url(url, 'http://lys.jsnc.gov.cn/jyfx/jygg/'):
                continue

            title = handle_str.replace_escape(row.get('proName')).strip()
            if params['t'] == 1:
                pubTime = None
            else:
                pubTime = row.get('turnoverTime')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
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

        if params['pubTime'] is None:
            params['pubTime'] = soup.select_one('#jy-item-title-date').get_text(strip=True)

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
