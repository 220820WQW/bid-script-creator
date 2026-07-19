# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import uuid
import hashlib
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
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://zc.ceesc.cn:19300",
    "Pragma": "no-cache",
    "Referer": "https://zc.ceesc.cn:19300/purchase/notice/adminNotice?type=plan",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-Sign": "DBECA823E647C09F689832A5FCF0D10A_4d8548e3be1c491592568a492e892c0d",
    "X-TIMESTAMP": "1782899394745",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
COOKIES = {}

SECRET = "dd05f1c54d63749eda95f9fa6d49v442a"


def build_uuid():
    return uuid.uuid4().hex


def make_x_sign(dp):
    base = json.dumps(dp, ensure_ascii=False, separators=(",", ":"))
    return hashlib.md5((base + SECRET).encode("utf-8")).hexdigest().upper() + "_" + build_uuid()


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 采购计划
            {
                "url": "https://zc.ceesc.cn:19300/jeecgboot/jeecg-system/consumer/notice/api/queryNoticeAllByPage?dp=7390cdb85b2747379bc4c8d139b700b0",
                "page_number": 1,
                'data': {
                    "column": "createTime",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 10,
                    "type": "plan"
                },
            },
            # 招标公告
            {
                "url": "https://zc.ceesc.cn:19300/jeecgboot/jeecg-system/consumer/notice/api/queryNoticeAllByPage?dp=0c14c9103bc0481abf8b3498e6440ceb",
                "page_number": 5,
                'data': {
                    "column": "createTime",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 10,
                    "type": "zb"
                },
            },
            # 采购公告
            {
                "url": "https://zc.ceesc.cn:19300/jeecgboot/jeecg-system/consumer/notice/api/queryNoticeAllByPage?dp=961d973c0499453d8db49561b4b7091d",
                "page_number": 10,
                'data': {
                    "column": "createTime",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 10,
                    "type": "procure"
                }
            },
            # 推荐中标候选人公示
            {
                "url": "https://zc.ceesc.cn:19300/jeecgboot/jeecg-system/consumer/notice/api/queryNoticeAllByPage?dp=8931728be43846f6a38ded06dd7c4aeb",
                "page_number": 1,
                'data': {
                    "column": "createTime",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 10,
                    "type": "candidatePublicity"
                }
            },
            # 中标（成交）结果公示
            {
                "url": "https://zc.ceesc.cn:19300/jeecgboot/jeecg-system/consumer/notice/api/queryNoticeAllByPage?dp=57f865774a23493e8c400d8dcc8b1aa3",
                "page_number": 1,
                'data': {
                    "column": "createTime",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 10,
                    "type": "transactionResults"
                }
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                p['data']['pageNo'] = index
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy()
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        dp = build_uuid()
        headers = HEADERS.copy()
        headers["X-Sign"] = make_x_sign(dp)

        resp = auto_request(url=params['url'], headers=headers, cookies=COOKIES, json=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('result').get('records')

        for row in rows:
            id = row.get('id')
            url = f"https://zc.ceesc.cn:19300/purchase/notice/LookNotice?id={id}&type={params['data']['type']}"

            title = row.get('title')
            pubTime = row.get('createTime')

            content = row.get('contents')
            content = handle_str.completion_url(str(content), params['url'])
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'content': content})

        return ret_list

    def get_content(self, params: dict):
        if params.get('content'):
            return params

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.v_news_content')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
