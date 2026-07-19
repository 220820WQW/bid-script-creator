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
                "url": "https://www.gongshan.gov.cn/html/ywdt/tzgg/",
                "page_number": 1,
            },
            # 许可事项
            {
                "url": "https://www.gongshan.gov.cn/zfb/xksx/",
                "page_number": 1,
            },
            # 结果公示
            {
                "url": "https://www.gongshan.gov.cn/zfb/jggs/",
                "page_number": 1,
            },
            # 集中式饮用水水源保护专项行动
            {
                "url": "https://www.gongshan.gov.cn/zfb/jzsyyssybhzxxd/",
                "page_number": 1,
            },
            # 保障性住房信息专栏
            {
                "url": "https://www.gongshan.gov.cn/zfb/bzxzfxxzl/",
                "page_number": 1,
            },
            # 生态环境
            {
                "url": "https://www.gongshan.gov.cn/sthjj/sthj/",
                "page_number": 1,
            },
            # 法律法规和规范性文件
            {
                "url": "https://www.gongshan.gov.cn/zfb/flfghgfxwj/",
                "page_number": 1,
            },
            # 政府信息公开制度
            {
                "url": "https://www.gongshan.gov.cn/zfb/zfxxgkzd/",
                "page_number": 1,
            },
            # 国民经济和社会发展计划报告
            {
                "url": "https://www.gongshan.gov.cn/fgjxj/zcwj/",
                "page_number": 1,
            },
            # 政策文件
            {
                "url": "https://www.gongshan.gov.cn/jytyj/zcwj/",
                "page_number": 1,
            },
            # 重点领域信息公开
            {
                "url": "https://www.gongshan.gov.cn/gaj/zdlyxxgk/",
                "page_number": 1,
            },
            # 养老服务
            {
                "url": "https://www.gongshan.gov.cn/mzj/ylfw/",
                "page_number": 1,
            },
            # 政策文件
            {
                "url": "https://www.gongshan.gov.cn/mzj/zcwj/",
                "page_number": 1,
            },
            # 政策文件
            {
                "url": "https://www.gongshan.gov.cn/czj/zcwj/",
                "page_number": 1,
            },
            # 财政资金直达基层
            {
                "url": "https://www.gongshan.gov.cn/czj/czzjzdjc/",
                "page_number": 1,
            },
            # 生态环境
            {
                "url": "https://www.gongshan.gov.cn/sthjj/sthj/",
                "page_number": 1,
            },
            # 其它信息
            {
                "url": "https://www.gongshan.gov.cn/zjj/qtxx/",
                "page_number": 1,
            },
            # 保障性住房
            {
                "url": "https://www.gongshan.gov.cn/zjj/bzxzf/",
                "page_number": 1,
            },
            # 重大事项
            {
                "url": "https://www.gongshan.gov.cn/slj/zdsx/",
                "page_number": 1,
            },
            # 行政执法公示
            {
                "url": "https://www.gongshan.gov.cn/whlyj/xzzfgs/",
                "page_number": 1,
            },
            # 审计工作
            {
                "url": "https://www.gongshan.gov.cn/sjj/sjgz/",
                "page_number": 1,
            },
            # 通知公告
            {
                "url": "https://www.gongshan.gov.cn/wsb/tzgg/",
                "page_number": 1,
            },
            # 通知公告
            {
                "url": "https://www.gongshan.gov.cn/ylbzj/tzgg/",
                "page_number": 1,
            },
            # 其它信息
            {
                "url": "https://www.gongshan.gov.cn/ylbzj/qtxx/",
                "page_number": 1,
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'],
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select('ul.text-big li') or soup.select('.gkmus2-1 ul li')

        for row in rows:
            a_tag = row.select_one('a')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.get_text(strip=True)
            pubTime = (row.select_one('span.float-right') or row.select_one('span')).get_text(strip=True)
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.m-4')

        if attach := soup.select_one('.attach'):
            content.append(attach)

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
