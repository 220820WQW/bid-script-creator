# -*- coding: UTF-8 -*-
import re
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
            # 公示公告
            {
                "url": "http://wsjsw.linyi.gov.cn/gsgg.htm",
                "page_number": 1,
                "t": 1
            },
            # 通知公告
            {
                "url": "http://wsjsw.linyi.gov.cn/xxgk1/xzql/_ssj__ygk_jg/tzgg.htm",
                "page_number": 1,
                "t": 2
            },
            # 抽查计划
            {
                "url": "http://wsjsw.linyi.gov.cn/xxgk1/xzql/_ssj__ygk_jg/ccjh.htm",
                "page_number": 1,
                "t": 2
            },
            # 人大代表建议办理结果
            {
                "url": "http://wsjsw.linyi.gov.cn/xxgk1/jyta/rddbjybljg.htm",
                "page_number": 1,
                "t": 2
            },
            # 政协委员提案办理结果
            {
                "url": "http://wsjsw.linyi.gov.cn/xxgk1/jyta/zxwytabljg.htm",
                "page_number": 1,
                "t": 2
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

        soup = BeautifulSoup(resp.text, "html.parser")

        if params['t'] == 1:
            rows = soup.select('li[id^="line_u9_"]')

            for row in rows:
                a_tag = row.select_one('a')
                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                title = a_tag.get_text(strip=True)
                pubTime = row.select_one('div.sx').get_text(strip=True)
                pubTime = handle_str.extract_and_validate_dates(pubTime)[0]
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 't': params['t']})

        if params['t'] == 2:
            rows = soup.select('div[class^="govnewslist"] > ul li')

            for row in rows:
                a_tag = row.select_one('a')
                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                title = a_tag.get_text(strip=True)
                pubTime = row.select_one('span').get_text(strip=True)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 't': params['t']})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div#vsb_content') or soup.select_one('.v_news_content') or soup.select_one('div[id*="vsb_content_"]')

        if params['t'] == 1:
            script_tag = content.select_one('script')
            if script_tag:
                script_text = script_tag.get_text()
                pdf_url = re.search(r'showVsbpdfIframe\("([^"]+)"', script_text)
                if pdf_url:
                    a_tag = soup.new_tag('a', href=urljoin(params['url'], pdf_url.group(1)), string='内容附件')
                    content.append(a_tag)
                    script_tag.decompose()

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
