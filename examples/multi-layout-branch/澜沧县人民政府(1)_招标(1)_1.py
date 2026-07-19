# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re

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
                "url": "https://www.lancang.gov.cn/zwxx/tzgg.htm",
                "page_number": 1,
                't': 1
            },
            # 政务信息
            {
                "url": "https://www.lancang.gov.cn/zwxx/zwxx.htm",
                "page_number": 1,
                't': 1
            },
            # 省政府信息
            {
                "url": "https://www.lancang.gov.cn/zwxx/szfxx.htm",
                "page_number": 1,
                "t": 1
            },

            # 政府信息公开制度
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/zfxxgkzd.htm",
                "page_number": 1,
                "t": 2
            },
            # 政府文件
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/zcwj/zfwj.htm",
                "page_number": 1,
                "t": 2
            },
            # 其他文件
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/zcwj/qtwj.htm",
                "page_number": 1,
                "t": 2
            },
            # 提案议案办理情况
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/tayablqk.htm",
                "page_number": 1,
                "t": 2
            },
            # 财政资金直达基层
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/czzjzdjc.htm",
                "page_number": 1,
                "t": 2
            },
            # 稳岗就业
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/wgjy.htm",
                "page_number": 1,
                "t": 2
            },
            # 乡村振兴
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/xczx.htm",
                "page_number": 1,
                "t": 2
            },
            # 养老服务
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/sbxx/ylfw.htm",
                "page_number": 1,
                "t": 2
            },
            # 社会救助
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/sbxx/shjz.htm",
                "page_number": 1,
                "t": 2
            },
            # 环保信息
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/hjbh/hbxx.htm",
                "page_number": 1,
                "t": 2
            },
            # 审批改革
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/spgg.htm",
                "page_number": 1,
                "t": 2
            },
            # 扶贫资金
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/czxx/fpzj.htm",
                "page_number": 1,
                "t": 2
            },
            # 审计结果公告
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/sjjggg.htm",
                "page_number": 1,
                "t": 2
            },
            # 公共资源交易
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/ggzyjy.htm",
                "page_number": 1,
                "t": 2
            },
            # 重大建设项目
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/zdjsxm.htm",
                "page_number": 1,
                "t": 2
            },
            # 国有土地上房屋征收补偿
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/gytdsfwzsbc.htm",
                "page_number": 1,
                "t": 2
            },
            # 国土空间规划
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/gtkjgh.htm",
                "page_number": 1,
                "t": 2
            },
            # 涉农补贴
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/snbt.htm",
                "page_number": 1,
                "t": 2
            },
            # 规划计划
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/ghjh.htm",
                "page_number": 1,
                "t": 2
            },
            # 重大决策
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/zdjc.htm",
                "page_number": 1,
                "t": 2
            },
            # 财政预决算及“三公”经费
            {
                "url": "https://www.lancang.gov.cn/zfxxgk/fdzdgknr/czyjsj_sg_jf.htm",
                "page_number": 1,
                "t": 2
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'], "t": p['t']
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        soup = BeautifulSoup(resp.text, "html.parser")

        if params['t'] == 1:
            rows = soup.select('div.newsList-content ul li')

            for row in rows:
                a_tag = row.select_one('a')
                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                title = a_tag.get_text(strip=True)
                pubTime = row.select_one('span').get_text(strip=True)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})
        if params['t'] == 2:
            rows = soup.select('ul.gklist li')

            for row in rows:
                a_tag = row.select_one('a')
                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                span = a_tag.select_one('span')
                pubTime = span.get_text(strip=True)
                span.decompose()
                title = a_tag.get_text(strip=True)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.v_news_content, #vsb_content')

        m = re.search(r'showVsbpdfIframe\("(.*?)",', str(content))
        if m:
            a_tag = soup.new_tag(name='a', href=m.group(1), string="内容附件")
            content.append(a_tag)

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
