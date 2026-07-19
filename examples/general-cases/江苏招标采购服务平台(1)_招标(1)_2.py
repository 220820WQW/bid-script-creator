# -*- coding: UTF-8 -*-
import json
from urllib.parse import urljoin, urlparse, quote

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
from datetime import datetime, date
import calendar


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
    "Origin": "https://www.jszbcg.com",
    "Pragma": "no-cache",
    "Referer": "https://www.jszbcg.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
COOKIES = {}


def get_last_month():
    dt = date.today()
    y, m, d = dt.year, dt.month, dt.day

    # 计算上月年月
    if m == 1:
        ly, lm = y - 1, 12
    else:
        ly, lm = y, m - 1

    # 获取上月最大天数
    last_month_max_day = calendar.monthrange(ly, lm)[1]
    # 取不超过上月最大天数的日期
    real_day = min(d, last_month_max_day)

    res = datetime(ly, lm, real_day)
    return res.strftime("%Y-%m-%d")


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 交易公开
            # 资格预审公告
            {
                "url": "https://api.jszbtb.com/DataSyncApi/HomeQulifyBulletin",
                "page_number": 1,
                "data": {
                    "PageSize": "20",
                    "CurrentPage": "1",
                    "Source": "zbcg",
                    "StartDateTime": "2026-06-01 00:00:00",
                    "EndDateTime": "2026-07-01 23:59:59",
                    "Keyword": ""
                },
                't': 1
            },
            # 招标/采购公告
            {
                "url": "https://api.jszbtb.com/DataSyncApi/HomeTenderBulletin",
                "page_number": 50,
                "data": {
                    "PageSize": "20",
                    "CurrentPage": "1",
                    "Source": "zbcg",
                    "StartDateTime": "2026-06-01 00:00:00",
                    "EndDateTime": "2026-07-01 23:59:59",
                    "Keyword": ""
                },
                't': 2
            },
            # 中标/成交候选人公示
            {
                "url": "https://api.jszbtb.com/DataSyncApi/HomeWinCandidateBulletin",
                "page_number": 20,
                "data": {
                    "PageSize": "20",
                    "CurrentPage": "1",
                    "Source": "zbcg",
                    "StartDateTime": "2026-06-01 00:00:00",
                    "EndDateTime": "2026-07-01 23:59:59",
                    "Keyword": ""
                },
                't': 3
            },
            # 招标/采购结果公示
            {
                "url": "https://api.jszbtb.com/DataSyncApi/HomeWinBidBulletin",
                "page_number": 30,
                "data": {
                    "PageSize": "20",
                    "CurrentPage": "1",
                    "Source": "zbcg",
                    "StartDateTime": "2026-06-01 00:00:00",
                    "EndDateTime": "2026-07-01 23:59:59",
                    "Keyword": ""
                },
                't': 4
            },
            # 更正/其它公告公示
            {
                "url": "https://api.jszbtb.com/DataSyncApi/AmendBulletin",
                "page_number": 6,
                "data": {
                    "PageSize": "20",
                    "CurrentPage": "1",
                    "Source": "zbcg",
                    "StartDateTime": "2026-06-01 00:00:00",
                    "EndDateTime": "2026-07-01 23:59:59",
                    "Keyword": ""
                },
                't': 5
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                p['data']['currentPage'] = str(index)
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy(), 't': p['t']
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        now = datetime.now().strftime("%Y-%m-%d") + " 23:59:59"
        last_month = get_last_month() + " 00:00:00"
        params['data']['EndDateTime'] = now
        params['data']['StartDateTime'] = last_month

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, params=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data').get('data')

        url_map = {
            1: "https://www.jszbcg.com/#/bulletindetail/QulifyBulletin/{}?release={}",
            2: "https://www.jszbcg.com/#/bulletindetail/TenderBulletin/{}?release={}",
            3: "https://www.jszbcg.com/#/bulletindetail/WinCandidateBulletin/{}?release={}",
            4: "https://www.jszbcg.com/#/bulletindetail/WinBidBulletin/{}?release={}",
            5: "https://www.jszbcg.com/#/bulletindetail/AmendBulletin/{}?release={}",
        }

        for row in rows:
            title = row.get('bulletinName') or row.get('publicityName')
            pubTime = row.get('create_time')

            if pubTime is None:
                t = row.get('amendbulletinissuetime')
                if "-" in t:
                    pubTime = t
                elif len(t) > 8:
                    t = t[:8]
                    pubTime = f"{t[:4]}-{t[4:6]}-{t[6:]}"
                else:
                    pubTime = datetime.now().strftime("%Y-%m-%d")

            id = row.get('id')
            release = handle_str.extract_and_validate_dates(pubTime)[0]
            url = url_map[params['t']].format(id, quote(json.dumps({"release": release}, separators=(',', ':'))))

            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 't': params['t']})

        return ret_list

    def get_content(self, params: dict):
        url_map = {
            1: "https://api.jszbtb.com/DataSyncApi/QulifyBulletin/id/{}",
            2: "https://api.jszbtb.com/DataSyncApi/TenderBulletin/id/{}",
            3: "https://api.jszbtb.com/DataSyncApi/WinCandidateBulletin/id/{}",
            4: "https://api.jszbtb.com/DataSyncApi/WinBidBulletin/id/{}",
            5: "https://api.jszbtb.com/DataSyncApi/AmendBulletin/id/{}",
        }
        url = url_map[params['t']].format(params['id'])
        resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        data = resp.json().get('data').get('data')[0]
        content = data.get('bulletincontent') or data.get('publicitycontent') or data.get('amendcontent')

        if attachement := data.get('attachement'):
            a_tag = f'<a href="{attachement.get("downloadUrl")}">{attachement.get("filename")}</a>'
            content += a_tag

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
