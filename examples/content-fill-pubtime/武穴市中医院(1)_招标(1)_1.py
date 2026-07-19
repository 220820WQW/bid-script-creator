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
    "accept": "text/html, */*; q=0.01",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/json;charset=UTF-8",
    "instance": "NEW2022062422043608344",
    "origin": "https://www.wxszyyy.cn",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://www.wxszyyy.cn/news/19884781.html",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}
COOKIES = {
    "sajssdk_2015_cross_ZQSensorsObjnew_user": "1",
    "sensorsdata2015jssdkcrossZQSensorsObj": "%7B%22distinct_id%22%3A%2219ef769e274d80-019aef36da24f15-26011b51-2073600-19ef769e2752db5%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%2C%22%24latest_landing_page%22%3A%22https%3A%2F%2Fwww.wxszyyy.cn%2F%22%7D%2C%22%24device_id%22%3A%2219ef769e274d80-019aef36da24f15-26011b51-2073600-19ef769e2752db5%22%7D"
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
            # 医院新闻
            {
                "url": "https://www.wxszyyy.cn/api/get_comp",
                "page_number": 1,
                'data': {
                    "compId": "c_static_001_P_72084-1749693041680",
                    "view": "news",
                    "params": "{\"size\":9,\"query\":[{\"valueName\":\"\",\"dataType\":\"array[category]\",\"operator\":\"in\",\"filter\":\"ignore-empty-check\",\"esField\":\"DETAIL_ES.es_multi_category_6d5k7017\",\"groupName\":\"数据展示条件,默认条件组\",\"groupEnd\":\"2,1\",\"field\":\"category_6d5k7017\",\"sourceType\":\"page\",\"logic\":\"and\",\"groupBegin\":\"1,2\",\"value\":\"19884781\",\"fieldType\":\"array\",\"configurable\":{\"sourceType\":\"page\",\"type\":\"normal\",\"value\":\"_detailId\"}}],\"header\":{\"Data-Query-Es-Field\":\"list,page,DETAIL_ES.es_symbol_text_2PVENH84,TEXT_DETAIL_ES.es_text_textarea_8B30N7U4,DETAIL_ES.es_date_prePublishTime\",\"Data-Query-Random\":0,\"Data-Query-Field\":\"list,page,text_2PVENH84,textarea_8B30N7U4,prePublishTime\"},\"from\":0,\"sort\":[],\"_detailId\":\"19884781\"}"
                }
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy()
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, json=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select('div.p_leftData .p_list > div')
        rows.extend(soup.select('div.p_leftData .p_focus > div'))

        for row in rows:
            a_tag = row.select_one('h3 a')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.get_text(strip=True)
            if row.select_one('.cbox-6-0'):
                day = row.select_one('.e_timeFormat-7').get_text(strip=True)
                year = row.select_one('.e_timeFormat-8').get_text(strip=True)
                pubTime = f'{year}-{day}'
            else:
                pubTime = None
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.e_richText-32')

        if params['pubTime'] is None:
            t = soup.select_one('.e_timeFormat-21')
            params['pubTime'] = handle_str.extract_and_validate_dates(t.text)[0]

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
