# -*- coding: UTF-8 -*-
import re
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
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": "http://www.hgggzy.com",
    "Pragma": "no-cache",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}
COOKIES = {
    "safedog-flow-item": "34DC20FC6817E1264BF0D63F6169288C"
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
            # 招标文件提前公示
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "newsid=1212"
                },
                't': 1
            },
            # 招标计划
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "newsid=702&jh=1"
                },
                't': 2
            },
            # 招标公告
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "jsgc=0100000&newsid=700"
                },
                't': 3
            },
            # 答疑澄清
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "jsgc=00110000"
                },
                't': 4
            },
            # 评标结果公示
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "jsgc=00000100&newsid=701"
                },
                't': 5
            },
            # 中标结果公告
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "jsgc=00000010"
                },
                't': 6
            },

            # 采购需求公示
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "zfcg=1000000&newsid=404"
                },
                't': 7
            },
            # 招标公告
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "zfcg=0100000000&newsid=400"
                },
                't': 8
            },
            # 澄清修改
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "zfcg=0010000000&newsid=403"
                },
                't': 9
            },
            # 中标结果公告
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "zfcg=0000011&newsid=401"
                },
                't': 10
            },
            # 终止公告
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "zfcg=00000000001"
                },
                't': 11
            },

            # 出让公告
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "tdjy=0100000&newsid=500"
                },
                't': 12
            },
            # 出让结果
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "tdjy=00000110&newsid=501"
                },
                't': 13
            },
            # 协议出让结果公示
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "tdjy=00000100000&newsid=505"
                },
                't': 14
            },

            # 交易公告
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "cqjy=0100000&newsid=300"
                },
                't': 15
            },
            # 成交结果公示
            {
                "url": "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsLists",
                "page_number": 1,
                'data': {
                    "KW": "",
                    "pageNumber": 1,
                    "pageSize": 10,
                    "searchContent": False,
                    "subIndex": 0,
                    "u": "cqjy=00000110&newsid=301"
                },
                't': 16
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy(), 't': p['t']
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        data = json.dumps(params['data'], separators=(',', ':'))
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, data=data)
        if 400 <= resp.status_code <= 599:
            return ret_list

        data = resp.json().get('outDatas')[0]
        rows = data.get('rows')

        if params['t'] == 1:
            for row in rows:
                id = row.get('id')
                webKind = row.get('webKind')
                url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl="

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 't': params['t']})
        if params['t'] == 2:
            for row in rows:
                url = row.get('goUrl')
                if url:
                    id = re.search(r'id=(.*?)&', url).group(1)
                else:
                    id = row.get('id')
                    webKind = row.get('webKind')
                    url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl="

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 't': params['t']})
        if params['t'] == 3:
            for row in rows:
                id = row.get('nid')
                webKind = row.get('webKind')
                url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl="

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 'webKind': webKind, 't': params['t']})
        if params['t'] == 4:
            for row in rows:
                id = row.get('nid')
                webKind = row.get('webKind')
                bydyUrl = row.get('bydyUrl')
                url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl={bydyUrl}"

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 'webKind': webKind, 't': params['t']})
        if params['t'] == 5:
            for row in rows:
                id = row.get('nid')
                webKind = row.get('webKind')
                url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl="

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 'webKind': webKind, 't': params['t']})
        if params['t'] == 6:
            for row in rows:
                id = row.get('nid')
                webKind = row.get('webKind')
                url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl="

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 'webKind': webKind, 't': params['t']})

        if params['t'] == 7:
            for row in rows:
                id = row.get('nid')
                webKind = row.get('webKind')
                url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl="

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 'webKind': webKind, 't': params['t']})
        if params['t'] == 8:
            for row in rows:
                id = row.get('nid')
                webKind = row.get('webKind')
                url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl=&t={params['t']}"

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 'webKind': webKind, 't': params['t']})
        if params['t'] == 9:
            for row in rows:
                id = row.get('nid')
                webKind = row.get('webKind')
                bydyUrl = row.get('bydyUrl')
                url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl={bydyUrl}"

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 'webKind': webKind, 't': params['t']})
        if params['t'] == 10:
            for row in rows:
                id = row.get('nid')
                webKind = row.get('webKind')
                url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl=&t={params['t']}"

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 'webKind': webKind, 't': params['t']})
        if params['t'] == 11:
            for row in rows:
                id = row.get('nid')
                webKind = row.get('webKind')
                bydyUrl = row.get('bydyUrl')
                url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl={bydyUrl}"

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 'webKind': webKind, 't': params['t']})

        if params['t'] == 12:
            for row in rows:
                id = row.get('nid')
                webKind = row.get('webKind')
                url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl=&t={params['t']}"

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 'webKind': webKind, 't': params['t']})
        if params['t'] == 13:
            for row in rows:
                id = row.get('nid')
                webKind = row.get('webKind')
                url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl=&t={params['t']}"

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 'webKind': webKind, 't': params['t']})
        if params['t'] == 14:
            for row in rows:
                id = row.get('nid')
                webKind = row.get('webKind')
                url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl=&t={params['t']}"

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 'webKind': webKind, 't': params['t']})

        if params['t'] == 15:
            for row in rows:
                id = row.get('nid')
                webKind = row.get('webKind')
                url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl=&t={params['t']}"

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 'webKind': webKind, 't': params['t']})
        if params['t'] == 16:
            for row in rows:
                id = row.get('nid')
                webKind = row.get('webKind')
                url = f"http://www.hgggzy.com/web/#/Sub/NewsDetail?id={id}&webKind={webKind}&bydyUrl=&t={params['t']}"

                title = row.get('title')
                pubTime = row.get('pubdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 'webKind': webKind, 't': params['t']})

        return ret_list

    def get_content(self, params: dict):
        if params['t'] == 1:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetailContent"
            d = {"id": params['id']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            content = resp.json().get('outDatas')[0].get('content')
        elif params['t'] == 2:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetailContent"
            d = {"id": params['id']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            content = resp.json().get('outDatas')[0].get('content')
        elif params['t'] == 3:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetail"
            d = {"id": params['id'], 'webKind': params['webKind']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            content = resp.json().get('outDatas')[0].get('zbggContent')
        elif params['t'] == 4:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetail"
            d = {"id": params['id'], 'webKind': params['webKind']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            content = resp.json().get('outDatas')[0].get('zbggContent')
        elif params['t'] == 5:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetail"
            d = {"id": params['id'], 'webKind': params['webKind']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            content = resp.json().get('outDatas')[0].get('jggsContent')
        elif params['t'] == 6:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetail"
            d = {"id": params['id'], 'webKind': params['webKind']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            content = resp.json().get('outDatas')[0].get('jgggContent')

        elif params['t'] == 7:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetail"
            d = {"id": params['id'], 'webKind': params['webKind']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            content = resp.json().get('outDatas')[0].get('yggContent')
        elif params['t'] == 8:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetail"
            d = {"id": params['id'], 'webKind': params['webKind']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            content = resp.json().get('outDatas')[0].get('zbggContent')

            if zbggfjs := resp.json().get('outDatas')[0].get('zbggfjs'):
                isggcdjbid = resp.json().get('outDatas')[0].get('isggcdjbid')
                for item in zbggfjs:
                    fj_url = f'http://www.hgggzy.com/QDFile/XMFiles/{isggcdjbid}/{item.get("fileName")}'
                    a_tag = f'<a href="{fj_url}">{item.get("fileTitle")}</a>'
                    content += a_tag
        elif params['t'] == 9:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetail"
            d = {"id": params['id'], 'webKind': params['webKind']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            bydy = resp.json().get('outDatas')[0].get('ByDy')
            content = bydy[0].get('sDayiBuyiContent') if bydy else resp.json().get('outDatas')[0].get('zbggContent')
        elif params['t'] == 10:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetail"
            d = {"id": params['id'], 'webKind': params['webKind']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            content = resp.json().get('outDatas')[0].get('jggsContent')
        elif params['t'] == 11:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetail"
            d = {"id": params['id'], 'webKind': params['webKind']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            Zzgg = resp.json().get('outDatas')[0].get('Zzgg')
            content = Zzgg[0].get('sDayiBuyiContent') if Zzgg else resp.json().get('outDatas')[0].get('zbggContent')

        elif params['t'] == 12:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetail"
            d = {"id": params['id'], 'webKind': params['webKind']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            content = resp.json().get('outDatas')[0].get('zbggContent')
            if not content:
                u2 = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetailContent"
                d2 = {"id": params['id']}
                resp = auto_request(url=u2, headers=HEADERS, cookies=COOKIES, json=d2)
                if 400 <= resp.status_code <= 599:
                    return None
                content = resp.json().get('outDatas')[0].get('content')
        elif params['t'] == 13:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetail"
            d = {"id": params['id'], 'webKind': params['webKind']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            content = resp.json().get('outDatas')[0].get('jggsContent')
        elif params['t'] == 14:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetail"
            d = {"id": params['id'], 'webKind': params['webKind']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            content = resp.json().get('outDatas')[0].get('jggsContent')

        elif params['t'] == 15:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetail"
            d = {"id": params['id'], 'webKind': params['webKind']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            content = resp.json().get('outDatas')[0].get('zbggContent')
            if not content:
                u2 = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetailContent"
                d2 = {"id": params['id']}
                resp = auto_request(url=u2, headers=HEADERS, cookies=COOKIES, json=d2)
                if 400 <= resp.status_code <= 599:
                    return None
                content = resp.json().get('outDatas')[0].get('content')
        elif params['t'] == 16:
            u = "http://www.hgggzy.com/CeinApp/AppFirstPg.ashx?k=getnewsDetail"
            d = {"id": params['id'], 'webKind': params['webKind']}
            resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES, json=d)
            if 400 <= resp.status_code <= 599:
                return None
            content = resp.json().get('outDatas')[0].get('jggsContent')

        else:
            return None

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
