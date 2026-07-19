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
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": "https://www.baiyu.gov.cn",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://www.baiyu.gov.cn/wzlb/c/3587",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}
COOKIES = {
    "zh_choose": "n",
    "mozi-assist": "{%22show%22:false%2C%22audio%22:false%2C%22speed%22:%22middle%22%2C%22zomm%22:1%2C%22cursor%22:false%2C%22pointer%22:false%2C%22bigtext%22:false%2C%22overead%22:false}"
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
            # 公示公告
            {
                "url": "https://www.baiyu.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId",
                "page_number": 1,
                "data": {
                    "columnId": 3587,
                    "current": 1,
                    "size": 15,
                    "type": False
                },
                't': 1
            },

            # 政府信息公开制度
            {
                "url": "https://www.baiyu.gov.cn/governmentInfo/byx_zfxxgk/old-zfxxgkzd",
                "page_number": 1,
                "data": {},
                't': 2
            },

            # 空间规划
            {
                "url": "https://www.baiyu.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId",
                "page_number": 1,
                "data": {
                    "columnId": 10609,
                    "current": 1,
                    "size": 15,
                    "type": True
                },
                't': 1
            },
            # 批准结果信息
            {
                "url": "https://www.baiyu.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId",
                "page_number": 1,
                "data": {
                    "columnId": 77508,
                    "current": 1,
                    "size": 15,
                    "type": True
                },
                't': 1
            },
            # 重大设计变更信息
            {
                "url": "https://www.baiyu.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId",
                "page_number": 1,
                "data": {
                    "columnId": 77510,
                    "current": 1,
                    "size": 15,
                    "type": True
                },
                't': 1
            },
            # 质量安全监督信息
            {
                "url": "https://www.baiyu.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId",
                "page_number": 1,
                "data": {
                    "columnId": 77512,
                    "current": 1,
                    "size": 15,
                    "type": True
                },
                't': 1
            },
            # 自然资源
            {
                "url": "https://www.baiyu.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId",
                "page_number": 1,
                "data": {
                    "columnId": 95509,
                    "current": 1,
                    "size": 15,
                    "type": True
                },
                't': 1
            },
            # 教育信息
            {
                "url": "https://www.baiyu.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId",
                "page_number": 1,
                "data": {
                    "columnId": 77514,
                    "current": 1,
                    "size": 15,
                    "type": True
                },
                't': 1
            },
            # 乡村振兴
            {
                "url": "https://www.baiyu.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId",
                "page_number": 1,
                "data": {
                    "columnId": 77549,
                    "current": 1,
                    "size": 15,
                    "type": True
                },
                't': 1
            },
            # 社会保障
            {
                "url": "https://www.baiyu.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId",
                "page_number": 1,
                "data": {
                    "columnId": 77566,
                    "current": 1,
                    "size": 15,
                    "type": True
                },
                't': 1
            },
            # 就业服务
            {
                "url": "https://www.baiyu.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId",
                "page_number": 1,
                "data": {
                    "columnId": 77573,
                    "current": 1,
                    "size": 15,
                    "type": True
                },
                't': 1
            },
            # 生态环境
            {
                "url": "https://www.baiyu.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId",
                "page_number": 1,
                "data": {
                    "columnId": 77584,
                    "current": 1,
                    "size": 15,
                    "type": True
                },
                't': 1
            },
            # 涉农补贴
            {
                "url": "https://www.baiyu.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId",
                "page_number": 1,
                "data": {
                    "columnId": 77596,
                    "current": 1,
                    "size": 15,
                    "type": True
                },
                't': 1
            },
            # 社会救助
            {
                "url": "https://www.baiyu.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId",
                "page_number": 1,
                "data": {
                    "columnId": 77604,
                    "current": 1,
                    "size": 15,
                    "type": True
                },
                't': 1
            },
            # 养老服务
            {
                "url": "https://www.baiyu.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId",
                "page_number": 1,
                "data": {
                    "columnId": 97803,
                    "current": 1,
                    "size": 15,
                    "type": True
                },
                't': 1
            },
            # 建议提案
            {
                "url": "https://www.baiyu.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId",
                "page_number": 1,
                "data": {
                    "columnId": 10893,
                    "current": 1,
                    "size": 15,
                    "type": True
                },
                't': 1
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

        if params.get('data'):
            resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, json=params['data'])
        else:
            resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)

        if 400 <= resp.status_code <= 599:
            return ret_list

        if params['t'] == 1:
            rows = resp.json().get('data').get('records')

            for row in rows:
                id = row.get('id')
                columnFolder = row.get('columnFolder')
                url = f"https://www.baiyu.gov.cn/{columnFolder}/article/{id}"

                title = row.get('title')
                pubTime = row.get('time')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})
        if params['t'] == 2:
            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.select('.rgith > div > div.list-item')

            for row in rows:
                a_tag = row.select_one('a')
                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(params['url'], url):
                    continue

                title = a_tag.get_text(strip=True)
                pubTime = row.select_one(':scope > div').get_text(strip=True)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div#contentBox')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
