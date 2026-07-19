# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
from datetime import datetime

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
    "Content-Type": "application/json;charset=UTF-8",
    "Pragma": "no-cache",
    "Referer": "https://gtjm.csggzy.cn/trade-engine/trade/announcement",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
COOKIES = {
    "SESSION": "f6ffe072-5f72-4b87-a7f0-73668be8db26",
    "Hm_lvt_51c486a6139c81714f0477741711352b": "1782703411",
    "HMACCOUNT": "45C6B9EC77B6BA14",
    "Hm_lpvt_51c486a6139c81714f0477741711352b": "1782703423"
}


def compare_and_format_date(input_date_str: str):
    """处理输入日期字符串，判断是否大于当前日期"""
    today = datetime.now().date()
    supported_formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y年%m月%d日", "%Y/%m/%d", "%Y/%-m/%-d", "%Y.%m.%d"]

    if not input_date_str.strip():
        return today.strftime("%Y-%m-%d")

    input_date = None
    for fmt in supported_formats:
        try:
            input_date = datetime.strptime(input_date_str, fmt).date()
            break
        except ValueError:
            continue

    if input_date is None:
        return today.strftime("%Y-%m-%d")

    if input_date > today:
        return today.strftime("%Y-%m-%d")
    else:
        return input_date.strftime("%Y-%m-%d")

class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 公告信息
            # 土地 出让公告
            {
                "url": "https://gtjm.csggzy.cn/devops/queryNoticeInfoList?pageNumber={}&pageSize=8&resourcesType=TD&noticeType=GPPMGG&regionCodeEnum=ALL_REGION&publishEndTime=2026-06-29%2011%3A23%3A57&TEST_TYPE=1&sort=DESC",
                "page_number": 2,
                't': 1
            },
            # 土地 补充公告
            {
                "url": "https://gtjm.csggzy.cn/devops/queryNoticeInfoList?pageNumber={}&pageSize=8&resourcesType=TD&noticeType=BCGG&regionCodeEnum=ALL_REGION&publishEndTime=2026-06-29%2011%3A23%3A57&TEST_TYPE=1&sort=DESC",
                "page_number": 1,
                't': 1
            },

            # 矿业权 挂牌公告
            {
                "url": "https://gtjm.csggzy.cn/devops/queryNoticeInfoList?pageNumber={}&pageSize=8&resourcesType=CK&noticeType=GPGG&regionCodeEnum=ALL_REGION&publishEndTime=2026-06-29%2011%3A23%3A57&TEST_TYPE=1&sort=DESC",
                "page_number": 1,
                't': 2
            },
            # 矿业权 挂牌公告
            {
                "url": "https://gtjm.csggzy.cn/devops/queryNoticeInfoList?pageNumber={}&pageSize=8&resourcesType=CK&noticeType=BCGG&regionCodeEnum=ALL_REGION&publishEndTime=2026-06-29%2011%3A23%3A57&TEST_TYPE=1&sort=DESC",
                "page_number": 1,
                't': 2
            },

            # 土地竞买
            {
                "url": "https://gtjm.csggzy.cn/devops/landBidding/queryLandBidding?TEST_TYPE=2&pageNumber={}&pageSize=10&regionCodeEnum=ALL_REGION&sortField=GPJSSJ&sortWay=DESC",
                "page_number": 3,
                't': 3
            },
            # 矿业权竞买
            {
                "url": "https://gtjm.csggzy.cn/devops/mining/queryHangOutList?TEST_TYPE=2&pageNumber={}&pageSize=10&regionCodeEnum=ALL_REGION",
                "page_number": 1,
                't': 4
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'].format(index), 't': p['t']
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data')

        if params['t'] == 1 or params['t'] == 2:
            for row in rows:
                GGID = row.get('GGID')
                JYFS = row.get('JYFS')
                ZYLB = row.get('ZYLB')
                url = f"https://gtjm.csggzy.cn/trade-engine/trade/anndetail?id={GGID}&type={JYFS}&category={ZYLB}"

                title = row.get('GGMC')
                pubTime = row.get('GGFBSJ')
                pubTime = handle_str.extract_and_validate_dates(pubTime)[0]
                pubTime = compare_and_format_date(pubTime)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'JYFS': JYFS, "GGID": GGID, 't': params['t']})
        if params['t'] == 3 or params['t'] == 4:
            for row in rows:
                ZYID = row.get('ZYID')
                ZYLB = row.get('ZYLB')
                JYFS = row.get('JYFS')
                url = f"https://gtjm.csggzy.cn/trade-engine/trade/detail?id={ZYID}&category={ZYLB}&type={JYFS}"

                title = row.get('ZYBH')
                pubTime = row.get('GPKSSJ')
                pubTime = handle_str.extract_and_validate_dates(pubTime)[0]
                pubTime = compare_and_format_date(pubTime)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'ZYID': ZYID, 't': params['t']})

        return ret_list

    def get_content(self, params: dict):
        if params['t'] == 1:
            url = f"https://gtjm.csggzy.cn/devops/queryNoticeLandContentDetails?noticeId={params['GGID']}&transactionMode={params['JYFS']}&pageNumber=1&pageSize=10"
        elif params['t'] == 2:
            url = f"https://gtjm.csggzy.cn/devops/queryNoticeMiningContentDetails?noticeId={params['GGID']}&transactionMode={params['JYFS']}&pageNumber=1&pageSize=10"
        elif params['t'] == 3:
            url = f"https://gtjm.csggzy.cn/devops/landBidding/getAnnouncement?resourceId={params['ZYID']}"
        elif params['t'] == 4:
            url = f"https://gtjm.csggzy.cn/devops/mining/queryNoticeById?resourceId={params['ZYID']}"
        else:
            return None

        resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        obj = resp.json().get('queryNoticeContent') or resp.json().get('data')
        content = obj.get('GGNR')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
