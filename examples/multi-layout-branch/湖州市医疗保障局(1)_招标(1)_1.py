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


HEADERS = {}
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
                "url": "http://ybj.huzhou.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?parseType=bulidstatic&webId=3637&tplSetId=EbKoPMNj3HMqsVsx9bkxK&pageType=column&tagId=ajax1&editType=null&pageId=1229209163",
                "page_number": 1,
                't': 1
            },

            # 信息公开制度
            {
                "url": "http://ybj.huzhou.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?parseType=bulidstatic&webId=3637&tplSetId=EbKoPMNj3HMqsVsx9bkxK&pageType=column&tagId=%E4%BF%A1%E6%81%AF%E5%85%AC%E5%BC%80%E5%88%B6%E5%BA%A6list&editType=null&pageId=1229512877",
                "page_number": 1,
                't': 2
            },

            # 意见征集
            {
                "url": "http://ybj.huzhou.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?webId=3637&pageId=1229512877&parseType=bulidstatic&pageType=column&tagId=%E7%BB%84%E9%85%8D%E5%88%86%E7%B1%BBlist&tplSetId=EbKoPMNj3HMqsVsx9bkxK&paramJson=%7B%22pageNo%22%3A1%2C%22pageSize%22%3A15%2C%22search%22%3A%22%7B%5C%22xxgkId%5C%22%3A%5C%22C001-001%5C%22%2C%5C%22xxgkType%5C%22%3A%5C%22xxgk_combination%5C%22%2C%5C%22nodeId%5C%22%3A%5C%2211330500MB15011651%5C%22%2C%5C%22className%5C%22%3A%5C%22%5C%22%7D%22%7D",
                "page_number": 1,
                't': 3
            },
            # 意见反馈
            {
                "url": "http://ybj.huzhou.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?webId=3637&pageId=1229512877&parseType=bulidstatic&pageType=column&tagId=%E7%BB%84%E9%85%8D%E5%88%86%E7%B1%BBlist&tplSetId=EbKoPMNj3HMqsVsx9bkxK&paramJson=%7B%22pageNo%22%3A1%2C%22pageSize%22%3A15%2C%22search%22%3A%22%7B%5C%22xxgkId%5C%22%3A%5C%22C001-002%5C%22%2C%5C%22xxgkType%5C%22%3A%5C%22xxgk_combination%5C%22%2C%5C%22nodeId%5C%22%3A%5C%2211330500MB15011651%5C%22%2C%5C%22className%5C%22%3A%5C%22%5C%22%7D%22%7D",
                "page_number": 1,
                't': 3
            },
            # 重大决策执行
            {
                "url": "http://ybj.huzhou.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?webId=3637&pageId=1229512877&parseType=bulidstatic&pageType=column&tagId=%E7%BB%84%E9%85%8D%E5%88%86%E7%B1%BBlist&tplSetId=EbKoPMNj3HMqsVsx9bkxK&paramJson=%7B%22pageNo%22%3A1%2C%22pageSize%22%3A15%2C%22search%22%3A%22%7B%5C%22xxgkId%5C%22%3A%5C%22H001%5C%22%2C%5C%22xxgkType%5C%22%3A%5C%22xxgk_combination%5C%22%2C%5C%22nodeId%5C%22%3A%5C%2211330500MB15011651%5C%22%2C%5C%22className%5C%22%3A%5C%22%5C%22%7D%22%7D",
                "page_number": 1,
                't': 3
            },
            # 重点改革任务
            {
                "url": "http://ybj.huzhou.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?webId=3637&pageId=1229512877&parseType=bulidstatic&pageType=column&tagId=%E7%BB%84%E9%85%8D%E5%88%86%E7%B1%BBlist&tplSetId=EbKoPMNj3HMqsVsx9bkxK&paramJson=%7B%22pageNo%22%3A1%2C%22pageSize%22%3A15%2C%22search%22%3A%22%7B%5C%22xxgkId%5C%22%3A%5C%22F001%5C%22%2C%5C%22xxgkType%5C%22%3A%5C%22xxgk_combination%5C%22%2C%5C%22nodeId%5C%22%3A%5C%2211330500MB15011651%5C%22%2C%5C%22className%5C%22%3A%5C%22%5C%22%7D%22%7D",
                "page_number": 1,
                't': 3
            },
            # 医保领域重点改革信息
            {
                "url": "http://ybj.huzhou.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?webId=3637&pageId=1229512877&parseType=bulidstatic&pageType=column&tagId=%E7%BB%84%E9%85%8D%E5%88%86%E7%B1%BBlist&tplSetId=EbKoPMNj3HMqsVsx9bkxK&paramJson=%7B%22pageNo%22%3A1%2C%22pageSize%22%3A15%2C%22search%22%3A%22%7B%5C%22xxgkId%5C%22%3A%5C%22QQ001-005-005-005%5C%22%2C%5C%22xxgkType%5C%22%3A%5C%22xxgk_combination%5C%22%2C%5C%22nodeId%5C%22%3A%5C%2211330500MB15011651%5C%22%2C%5C%22className%5C%22%3A%5C%22%5C%22%7D%22%7D",
                "page_number": 1,
                't': 3
            },
            # 人大代表建议办理
            {
                "url": "http://ybj.huzhou.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?webId=3637&pageId=1229512877&parseType=bulidstatic&pageType=column&tagId=%E7%BB%84%E9%85%8D%E5%88%86%E7%B1%BBlist&tplSetId=EbKoPMNj3HMqsVsx9bkxK&paramJson=%7B%22pageNo%22%3A1%2C%22pageSize%22%3A15%2C%22search%22%3A%22%7B%5C%22xxgkId%5C%22%3A%5C%22W001-001%5C%22%2C%5C%22xxgkType%5C%22%3A%5C%22xxgk_combination%5C%22%2C%5C%22nodeId%5C%22%3A%5C%2211330500MB15011651%5C%22%2C%5C%22className%5C%22%3A%5C%22%5C%22%7D%22%7D",
                "page_number": 1,
                't': 3
            },
            # 政协委员提案办理
            {
                "url": "http://ybj.huzhou.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?webId=3637&pageId=1229512877&parseType=bulidstatic&pageType=column&tagId=%E7%BB%84%E9%85%8D%E5%88%86%E7%B1%BBlist&tplSetId=EbKoPMNj3HMqsVsx9bkxK&paramJson=%7B%22pageNo%22%3A1%2C%22pageSize%22%3A15%2C%22search%22%3A%22%7B%5C%22xxgkId%5C%22%3A%5C%22W001-002%5C%22%2C%5C%22xxgkType%5C%22%3A%5C%22xxgk_combination%5C%22%2C%5C%22nodeId%5C%22%3A%5C%2211330500MB15011651%5C%22%2C%5C%22className%5C%22%3A%5C%22%5C%22%7D%22%7D",
                "page_number": 1,
                't': 3
            },

        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'], 't': p['t']
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        html = resp.json().get('data').get('html')
        soup = BeautifulSoup(html, "html.parser")

        if params['t'] == 1:
            rows = soup.select('div.page-content > a')

            for row in rows:
                url = urljoin(params['url'], row.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                title = row.select_one('span').get_text(strip=True)
                pubTime = row.select_one('.main_222212').get_text(strip=True)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})
        if params['t'] == 2:
            rows = soup.select('div.page-content > li')

            for row in rows:
                a_tag = row.select_one('a')
                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                title = a_tag.get_text(strip=True)
                pubTime = row.select_one('b').get_text(strip=True)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})
        if params['t'] == 3:
            rows = soup.select('div.page-content .ajax-ul li')

            for row in rows:
                a_tag = row.select_one('a')
                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                # title = a_tag.get_text(strip=True)
                pubTime = row.select_one('.fr').get_text(strip=True)
                ret_list.append({'url': url, 'title': None, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div#aaa, div.zhengw, div#zhengw')

        if params['title'] is None:
            t = soup.select_one('.title1')
            params['title'] = t.get_text(strip=True)

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
