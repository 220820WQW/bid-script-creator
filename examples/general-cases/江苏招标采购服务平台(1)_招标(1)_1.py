# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

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
            # 公告公示
            # 招标/采购计划公告
            {
                "url": "https://api.jszbtb.com/DataGatewayApi/PublishBulletins",
                "page_number": 1,
                "data": {
                    "bulletinType": "5",
                    "industryCode": "",
                    "regionCode": "",
                    "startTime": "2026-06-01 00:00:00",
                    "endTime": "2026-7-1 23:59:59",
                    "keyword": "",
                    "currentPage": "1",
                    "pageSize": "20",
                    "source": "zbcg",
                    "Source": "zbcg"
                },
                't': 1
            },
            # 资格预审公告
            {
                "url": "https://api.jszbtb.com/DataGatewayApi/PublishBulletins",
                "page_number": 1,
                "data": {
                    "bulletinType": "0",
                    "industryCode": "",
                    "regionCode": "",
                    "startTime": "2026-06-01 00:00:00",
                    "endTime": "2026-7-1 23:59:59",
                    "keyword": "",
                    "currentPage": "1",
                    "pageSize": "20",
                    "source": "zbcg",
                    "Source": "zbcg"
                },
                't': 2
            },
            # 招标/采购公告
            {
                "url": "https://api.jszbtb.com/DataGatewayApi/PublishBulletins",
                "page_number": 70,
                "data": {
                    "bulletinType": "1",
                    "industryCode": "",
                    "regionCode": "",
                    "startTime": "2026-06-01 00:00:00",
                    "endTime": "2026-7-1 23:59:59",
                    "keyword": "",
                    "currentPage": "1",
                    "pageSize": "20",
                    "source": "zbcg",
                    "Source": "zbcg"
                },
                't': 3
            },
            # 中标/成交候选人公示
            {
                "url": "https://api.jszbtb.com/DataGatewayApi/PublishBulletins",
                "page_number": 20,
                "data": {
                    "bulletinType": "2",
                    "industryCode": "",
                    "regionCode": "",
                    "startTime": "2026-06-01 00:00:00",
                    "endTime": "2026-7-1 23:59:59",
                    "keyword": "",
                    "currentPage": "1",
                    "pageSize": "20",
                    "source": "zbcg",
                    "Source": "zbcg"
                },
                't': 4
            },
            # 招标/采购结果公示
            {
                "url": "https://api.jszbtb.com/DataGatewayApi/PublishBulletins",
                "page_number": 50,
                "data": {
                    "bulletinType": "3",
                    "industryCode": "",
                    "regionCode": "",
                    "startTime": "2026-06-01 00:00:00",
                    "endTime": "2026-7-1 23:59:59",
                    "keyword": "",
                    "currentPage": "1",
                    "pageSize": "20",
                    "source": "zbcg",
                    "Source": "zbcg"
                },
                't': 5
            },
            # 更正公告公示
            {
                "url": "https://api.jszbtb.com/DataGatewayApi/PublishBulletins",
                "page_number": 20,
                "data": {
                    "bulletinType": "4",
                    "industryCode": "",
                    "regionCode": "",
                    "startTime": "2026-06-01 00:00:00",
                    "endTime": "2026-7-1 23:59:59",
                    "keyword": "",
                    "currentPage": "1",
                    "pageSize": "20",
                    "source": "zbcg",
                    "Source": "zbcg"
                },
                't': 6
            },
            # 非公开招标理由公示
            {
                "url": "https://api.jszbtb.com/DataGatewayApi/PublishBulletins",
                "page_number": 1,
                "data": {
                    "bulletinType": "6",
                    "industryCode": "",
                    "regionCode": "",
                    "startTime": "2026-06-01 00:00:00",
                    "endTime": "2026-7-1 23:59:59",
                    "keyword": "",
                    "currentPage": "1",
                    "pageSize": "20",
                    "source": "zbcg",
                    "Source": "zbcg"
                },
                't': 7
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
        params['data']['endTime'] = now
        params['data']['startTime'] = last_month

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, params=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data').get('data')

        url_map = {
            1: "https://www.jszbcg.com/#/bulletinDetails/%E6%8B%9B%E6%A0%87%2F%E9%87%87%E8%B4%AD%E8%AE%A1%E5%88%92%E5%85%AC%E5%91%8A/{}?bulletinType={}",
            2: "https://www.jszbcg.com/#/bulletinDetails/%E8%B5%84%E6%A0%BC%E9%A2%84%E5%AE%A1%E5%85%AC%E5%91%8A/{}?bulletinType={}",
            3: "https://www.jszbcg.com/#/bulletinDetails/%E6%8B%9B%E6%A0%87%2F%E9%87%87%E8%B4%AD%E5%85%AC%E5%91%8A/{}?bulletinType={}",
            4: "https://www.jszbcg.com/#/bulletinDetails/%E4%B8%AD%E6%A0%87%2F%E6%88%90%E4%BA%A4%E5%80%99%E9%80%89%E4%BA%BA%E5%85%AC%E7%A4%BA/{}?bulletinType={}",
            5: "https://www.jszbcg.com/#/bulletinDetails/%E6%8B%9B%E6%A0%87%2F%E9%87%87%E8%B4%AD%E7%BB%93%E6%9E%9C%E5%85%AC%E7%A4%BA/{}?bulletinType={}",
            6: "https://www.jszbcg.com/#/bulletinDetails/%E6%9B%B4%E6%AD%A3%E5%85%AC%E5%91%8A%E5%85%AC%E7%A4%BA/{}?bulletinType={}",
            7: "https://www.jszbcg.com/#/bulletinDetails/%E9%9D%9E%E5%85%AC%E5%BC%80%E6%8B%9B%E6%A0%87%E7%90%86%E7%94%B1%E5%85%AC%E7%A4%BA/{}?bulletinType={}"
        }

        for row in rows:
            bulletinID = row.get('bulletinID')
            bulletinType = params['data']['bulletinType']
            url = url_map[params['t']].format(bulletinID, bulletinType)

            title = row.get('bulletinName')
            pubTime = row.get('noticeSendTime')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'bulletinID': bulletinID, 'bulletinType': bulletinType})

        return ret_list

    def get_content(self, params: dict):
        url = f"https://api.jszbtb.com/DataGatewayApi/PublishBulletin/BulletinType/{params['bulletinType']}/ID/{params['bulletinID']}"
        resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        data = resp.json().get('data')
        content = f'<a href="{data.get("signedPdfUrl")}">{data.get("bulletinName")}</a>'
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
