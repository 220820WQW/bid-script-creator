# -*- coding: UTF-8 -*-
import time
from urllib.parse import urljoin, urlparse, quote

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import subprocess, tempfile, os, json, sys
from bbSpider.utils import acquire_subjoin_path
from bbSpider.agent_pool import agent_pool


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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Referer": "http://ccgp-bingtuan.gov.cn/site/category",
    "Origin": "http://ccgp-bingtuan.gov.cn",
}
COOKIES = {}


def compute_cookie(html_text):
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8")
    try:
        tmp.write(html_text)
        tmp.close()
        result = subprocess.run(
            ["node", acquire_subjoin_path('compute_cookie.js'), tmp.name],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        return result.stdout.strip()
    finally:
        os.unlink(tmp.name)


def get_cookies(proxies=None):
    # 此网站只有此接口可以触发acw_sc__v2请求
    data = {"pageNo": 1, "pageSize": 15, "categoryCode": "btcgCorpsLevel"}
    r1 = request.post("http://ccgp-bingtuan.gov.cn/portal/category", json=data, headers=HEADERS, timeout=20, proxies=proxies, proxy_safety='http')
    cookies = dict(r1.cookies)
    if not cookies:
        return None

    if "renderData" in r1.text and "acw_sc__v2" in r1.text:
        acw_sc_v2 = compute_cookie(r1.text)
        if not acw_sc_v2:
            print(json.dumps({"error": "计算 acw_sc__v2 失败"}, ensure_ascii=False))
            sys.exit(1)

        cookies["acw_sc__v2"] = acw_sc_v2
        return cookies
    else:
        return None


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 网站头条
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 1,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "btcgSiteHeadNews",
                    "_t": 1784538105000
                },
                'parentId': 189168
            },
            # 兵团本级
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 1,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "btcgCorpsLevel",
                    "_t": 1784538544000
                },
                'parentId': 189168
            },
            # 师（市）级
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 1,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "btcgDivisionCity",
                    "_t": 1784538560000
                },
                'parentId': 189168
            },

            # 国家级
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 1,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "btcgContry",
                    "_t": 1784692035000
                },
                'parentId': 189170
            },
            # 兵团本级
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 1,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "btcgThisLevel",
                    "_t": 1784692162000
                },
                'parentId': 189170
            },
            # 兵团本级
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 1,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "btcgDivisionLevel",
                    "_t": 1784692173000
                },
                'parentId': 189170
            },

            # 采购意向
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 10,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "ZcyAnnouncement11",
                    "_t": 1784692328000,
                    "excludeDistrictPrefix": ["9Y"],
                    "isGov": True
                },
                'parentId': 189169
            },
            # 采购项目公告
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 10,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "ZcyAnnouncement2",
                    "_t": 1784692328000,
                    "excludeDistrictPrefix": ["9Y"],
                    "isGov": True
                },
                'parentId': 189169
            },
            # 采购公示
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 10,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "ZcyAnnouncement1",
                    "_t": 1784692328000,
                    "excludeDistrictPrefix": ["9Y"],
                    "isGov": True
                },
                'parentId': 189169
            },
            # 采购结果公告
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 10,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "ZcyAnnouncement4",
                    "_t": 1784692328000,
                    "excludeDistrictPrefix": ["9Y"],
                    "isGov": True
                },
                'parentId': 189169
            },
            # 采购合同公告
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 10,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "ZcyAnnouncement5",
                    "_t": 1784692328000,
                    "excludeDistrictPrefix": ["9Y"],
                    "isGov": True
                },
                'parentId': 189169
            },
            # 澄清变更公告
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 10,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "ZcyAnnouncement3",
                    "_t": 1784692328000,
                    "excludeDistrictPrefix": ["9Y"],
                    "isGov": True
                },
                'parentId': 189169
            },
            # 履约验收
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 1,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "ZcyAnnouncement6",
                    "_t": 1784692328000,
                    "excludeDistrictPrefix": ["9Y"],
                    "isGov": True
                },
                'parentId': 189169
            },
            # 电子卖场公告
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 30,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "ZcyAnnouncement8",
                    "_t": 1784692328000,
                    "excludeDistrictPrefix": ["9Y"],
                    "isGov": True
                },
                'parentId': 189169
            },
            # 采购公告工程项目公告
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 10,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "ZcyAnnouncement50",
                    "_t": 1784692328000,
                    "excludeDistrictPrefix": ["9Y"],
                    "isGov": True
                },
                'parentId': 189169
            },
            # 框架协议征集公告
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 1,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "ZcyAnnouncement12",
                    "_t": 1784692328000,
                    "excludeDistrictPrefix": ["9Y"],
                    "isGov": True
                },
                'parentId': 189169
            },
            # 框架协议入围结果公告
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 1,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "ZcyAnnouncement13",
                    "_t": 1784692328000,
                    "excludeDistrictPrefix": ["9Y"],
                    "isGov": True
                },
                'parentId': 189169
            },
            # 框架协议成交结果公告
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 1,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "ZcyAnnouncement14",
                    "_t": 1784692328000,
                    "excludeDistrictPrefix": ["9Y"],
                    "isGov": True
                },
                'parentId': 189169
            },
            # 框架协议成交结果汇总公告
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 1,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "ZcyAnnouncement16",
                    "_t": 1784692328000,
                    "excludeDistrictPrefix": ["9Y"],
                    "isGov": True
                },
                'parentId': 189169
            },
            # 非政府采购公告
            {
                "url": "http://ccgp-bingtuan.gov.cn/portal/category",
                "page_number": 10,
                'data': {
                    "pageNo": 1,
                    "pageSize": 15,
                    "categoryCode": "ZcyAnnouncement9",
                    "_t": 1784692328000,
                    "excludeDistrictPrefix": ["9Y"],
                    "isGov": True
                },
                'parentId': 189169
            },

        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                p['data']['pageNo'] = index
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy(), 'parentId': p['parentId']
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        for _ in range(8):
            try:
                proxies = agent_pool(params['url'])['http']
                cookies = get_cookies(proxies)
                if cookies:
                    break
                time.sleep(1)
            except:
                time.sleep(1)
                continue
        else:
            return ret_list

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=cookies, json=params['data'], proxies=proxies)
        if 400 <= resp.status_code <= 599:
            return ret_list

        try:
            rows = resp.json().get('result', {}).get('data', {}).get('data', [])
        except:
            return ret_list

        for row in rows:
            articleId = row.get('articleId')
            url = f"http://ccgp-bingtuan.gov.cn/site/detail?parentId={params['parentId']}&articleId={articleId}"

            title = row.get('title')
            pubTime = row.get('publishDate')
            pubTime = handle_str.time_stamp(pubTime)
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'articleId': articleId, 'parentId': params['parentId']})

        return ret_list

    def get_content(self, params: dict):
        url = f"http://ccgp-bingtuan.gov.cn/portal/detail?articleId={quote(params['articleId'], safe='')}&parentId={params['parentId']}&timestamp=1784538368"

        for _ in range(8):
            try:
                proxies = agent_pool(params['url'])['http']
                cookies = get_cookies(proxies)
                if cookies:
                    break
                time.sleep(1)
            except:
                time.sleep(1)
                continue
        else:
            return None

        resp = auto_request(url, headers=HEADERS, cookies=cookies, proxies=proxies)
        if 400 <= resp.status_code <= 599:
            return None

        try:
            data = resp.json().get('result', {}).get('data', {})
        except:
            return None

        content = data.get('content')

        if attachmentList := data.get('attachmentList'):
            for attachment in attachmentList:
                a_tag = f'<a href="{attachment.get("path")}">{attachment.get("name")}</a>'
                content += a_tag

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
