# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str


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
    "accept": "text/plain, */*; q=0.01",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://zyhsf.youzhicai.com",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://zyhsf.youzhicai.com/newTopic/purchase.html?type=1",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    # "x-csrf-token": "w93IgMJIm4Z7RuhtA8tHEoU83CzJ1ApnbdXs4Aqb",
    "x-requested-with": "XMLHttpRequest"
}
COOKIES = {
    # "Hm_lvt_9511d505b6dfa0c133ef4f9b744a16da": "1782810990",
    # "HMACCOUNT": "45C6B9EC77B6BA14",
    # "Hm_lpvt_9511d505b6dfa0c133ef4f9b744a16da": "1782811212",
    # "XSRF-TOKEN": "eyJpdiI6InNUbklVd3JJRW1TSmt6TGd4VFpqVHc9PSIsInZhbHVlIjoicVp3cWJWdUNQTzcrcG5OSVJ3bmpUMURnQjBxRldLeDJGOWJqUEN6djV4ZHR4dzNaQmh4K04zNHRBN3JTSU13VmRyRmFrNEJOXC9FdTIwQ2d2ZklyOWtRPT0iLCJtYWMiOiIwZjczNGNiZDg1ZjFlMzJiODE4N2E1NzQwN2VkYzMyYWEyMDQ0MDIzNzJiYTk3Mzg3ZmQ1M2ZhNDA4OGE3NmUyIn0%3D",
    # "laravel_session": "eyJpdiI6IllNU284S1NcL0lBODFlTXE3UEQ5a0pBPT0iLCJ2YWx1ZSI6InVydHM4czZIeEdaK0JER2k1Mm9MV2FQXC8zaGlMeEpLcjJUR3lONCtLTGUxbTQ2bldpajhCbVpIRUpUekJzTzdjWWJFN0pyYkV3NGtGbXdBV2pHbkt4Zz09IiwibWFjIjoiYjVjNzA0NWE4ZjU2ZDc0NzU3ZmU4NWY1MWE3NTNmMTkzOTUzYTEzMTgzYjgzY2U0MDViMDljOGY2ODYxOGJjNSJ9"
}


def get_headers_and_cookies():
    for _ in range(8):
        headers = HEADERS.copy()
        url = "https://zyhsf.youzhicai.com/"
        response = request.get(url, headers=headers)
        if response.status_code != 200:
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.select_one('meta[name="csrf-token"]').get('content')

        headers['x-csrf-token'] = csrf_token
        cookies = response.cookies.get_dict()
        return headers, cookies
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
            # 招标信息
            {
                "url": "https://zyhsf.youzhicai.com/newtopic/data-list",
                "page_number": 3,
                "data": {
                    "pageIndex": "1",
                    "id": "8312F123-CC36-F700-91DA-D7E911B8EB3D",
                    "type": "1",
                    "companyId": "",
                    "title": "",
                    "ntype": "",
                    "start_time": "",
                    "end_time": "",
                    "child": ""
                }
            },
            # 非招标信息
            {
                "url": "https://zyhsf.youzhicai.com/newtopic/data-list",
                "page_number": 3,
                "data": {
                    "pageIndex": "2",
                    "id": "8312F123-CC36-F700-91DA-D7E911B8EB3D",
                    "type": "2",
                    "companyId": "",
                    "title": "",
                    "ntype": "",
                    "start_time": "",
                    "end_time": "",
                    "child": ""
                }
            },
            # 结果公示
            {
                "url": "https://zyhsf.youzhicai.com/newtopic/data-list",
                "page_number": 3,
                "data": {
                    "pageIndex": "1",
                    "id": "8312F123-CC36-F700-91DA-D7E911B8EB3D",
                    "type": "1,2",
                    "companyId": "",
                    "title": "",
                    "ntype": "",
                    "start_time": "",
                    "end_time": "",
                    "child": ""
                }
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                p['data']['pageIndex'] = str(index)
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy()
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        v = get_headers_and_cookies()
        if v is None:
            return ret_list

        headers, cookies = v

        resp = auto_request(url=params['url'], headers=headers, cookies=cookies, data=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('list')

        for row in rows:
            noticeId = row.get('noticeId')
            url = row.get('Url')
            url = urljoin(params['url'], url)

            title = row.get('noticeTitle')
            pubTime = row.get('startTime')
            pubTime = handle_str.extract_and_validate_dates(pubTime)[0]
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, "noticeId": noticeId})

        return ret_list

    def get_content(self, params: dict):
        v = get_headers_and_cookies()
        if v is None:
            return None

        headers, cookies = v

        url = f"https://www.youzhicai.com/msnotice/NoticeIndexCompany?id={params['noticeId']}&noticeCateId=1&color="
        resp = auto_request(url=url, headers=headers, cookies=cookies)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.Container.content')

        if tabPanel := soup.select_one('.tabPanel'):
            content.append(tabPanel)

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
