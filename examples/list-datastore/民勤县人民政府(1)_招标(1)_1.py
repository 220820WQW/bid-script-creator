# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re


def auto_request(url, params=None, data=None, json=None, proxy_safety=None, **kwargs):
    """
    自动区分 GET / POST
    :param url: 请求地址
    :param params: URL 查询参数
    :param data: 表单 data
    :param json: JSON 请求体
    :param proxy_safety: 代理类型: http / https
    :param kwargs: 自动接收 headers / cookies / timeout / allow_redirects / verify / proxies 等
    """
    proxy_safety = proxy_safety if proxy_safety else urlparse(url).scheme
    # 有 data 或 json 自动走 POST
    if data is not None or json is not None:
        resp = request.post(url, params=params, data=data, json=json, proxy_safety=proxy_safety, **kwargs)
    # 无请求体 走 GET
    else:
        resp = request.get(url, params=params, proxy_safety=proxy_safety, **kwargs)

    resp.encoding = resp.apparent_encoding
    return resp


def is_same_origin_url(url_a: str, url_b: str):
    """判断两个URL是否同源（仅对比域名，忽略www和大小写）"""
    # 定义附件后缀
    suffix = {".pdf", ".doc", ".docx", ".xls", ".xlsx"}

    # 检查是否为附件
    def _is_attachment(url: str) -> bool:
        path = urlparse(url).path.lower()
        return path.endswith(tuple(suffix))

    if _is_attachment(url_a) or _is_attachment(url_b):
        return False

    # 同源域名判断
    domain_a = urlparse(url_a).netloc.lower().removeprefix('www.')
    domain_b = urlparse(url_b).netloc.lower().removeprefix('www.')
    return domain_a == domain_b


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
            # 国务院和国务院办公厅文件
            {
                "url": "https://www.minqin.gov.cn/col/col3630/index.html",
                "page_number": 1,
            },
            # 省政府和省政府办公厅文件
            {
                "url": "https://www.minqin.gov.cn/col/col3631/index.html",
                "page_number": 1,
            },
            # 市政府和市政府办公室文件
            {
                "url": "https://www.minqin.gov.cn/col/col3632/index.html",
                "page_number": 1,
            },
            # 行政许可
            {
                "url": "https://www.minqin.gov.cn/col/col3653/index.html",
                "page_number": 1,
            },
            # 双随机一公开
            {
                "url": "https://www.minqin.gov.cn/col/col28377/index.html",
                "page_number": 1,
            },
            # 行政处罚
            {
                "url": "https://www.minqin.gov.cn/col/col28376/index.html",
                "page_number": 1,
            },
            # 惠民、惠农、惠企政策信息
            {
                "url": "https://www.minqin.gov.cn/col/col3734/index.html",
                "page_number": 1,
            },
            # 农田水利工程建设运营
            {
                "url": "https://www.minqin.gov.cn/col/col3756/index.html",
                "page_number": 1,
            },
            # 脱贫攻坚与乡村振兴
            {
                "url": "https://www.minqin.gov.cn/col/col31932/index.html",
                "page_number": 1,
            },
            # 征地信息
            {
                "url": "https://www.minqin.gov.cn/col/col3773/index.html",
                "page_number": 1,
            },
            # 征收土地补偿安置
            {
                "url": "https://www.minqin.gov.cn/col/col3774/index.html",
                "page_number": 1,
            },
            # 房地产市场信息
            {
                "url": "https://www.minqin.gov.cn/col/col3771/index.html",
                "page_number": 1,
            },
            # 老旧小区改造
            {
                "url": "https://www.minqin.gov.cn/col/col3772/index.html",
                "page_number": 1,
            },
            # 政策法规
            {
                "url": "https://www.minqin.gov.cn/col/col3767/index.html",
                "page_number": 1,
            },
            # 宅基地使用情况审核
            {
                "url": "https://www.minqin.gov.cn/col/col3761/index.html",
                "page_number": 1,
            },
            # 贯彻落实农业农村政策
            {
                "url": "https://www.minqin.gov.cn/col/col3754/index.html",
                "page_number": 1,
            },
            # 饮用水水源
            {
                "url": "https://www.minqin.gov.cn/col/col3690/index.html",
                "page_number": 1,
            },
            # 供水厂出水
            {
                "url": "https://www.minqin.gov.cn/col/col3693/index.html",
                "page_number": 1,
            },
            # 用户水龙头水质
            {
                "url": "https://www.minqin.gov.cn/col/col3695/index.html",
                "page_number": 1,
            },

            # 国家政策
            {
                "url": "https://www.minqin.gov.cn/col/col3781/index.html",
                "page_number": 1,
            },
            # 省级政策
            {
                "url": "https://www.minqin.gov.cn/col/col3782/index.html",
                "page_number": 1,
            },
            # 市级政策
            {
                "url": "https://www.minqin.gov.cn/col/col3783/index.html",
                "page_number": 1,
            },
            # 县级政策
            {
                "url": "https://www.minqin.gov.cn/col/col3786/index.html",
                "page_number": 1,
            },
            # 扶贫政策
            {
                "url": "https://www.minqin.gov.cn/col/col3808/index.html",
                "page_number": 1,
            },
            # 帮扶措施与扶贫资金安排
            {
                "url": "https://www.minqin.gov.cn/col/col3812/index.html",
                "page_number": 1,
            },
            # 防范化解重大风险信息
            {
                "url": "https://www.minqin.gov.cn/col/col3821/index.html",
                "page_number": 1,
            },
            # 重大项目建设
            {
                "url": "https://www.minqin.gov.cn/col/col3920/index.html",
                "page_number": 1,
            },
            # 养老服务通用政策
            {
                "url": "https://www.minqin.gov.cn/col/col3944/index.html",
                "page_number": 1,
            },
            # 养老服务行业管理信息
            {
                "url": "https://www.minqin.gov.cn/col/col3945/index.html",
                "page_number": 1,
            },
            # 农村集体土地征收
            {
                "url": "https://www.minqin.gov.cn/col/col3963/index.html",
                "page_number": 1,
            },
            # 污染源信息
            {
                "url": "https://www.minqin.gov.cn/col/col3965/index.html",
                "page_number": 1,
            },
            # 重大建设项目环境管理
            {
                "url": "https://www.minqin.gov.cn/col/col3967/index.html",
                "page_number": 1,
            },
            # 扶贫资金
            {
                "url": "https://www.minqin.gov.cn/col/col4075/index.html",
                "page_number": 1,
            },
            # 扶贫项目
            {
                "url": "https://www.minqin.gov.cn/col/col4077/index.html",
                "page_number": 1,
            },
            # 重大决策预公开
            {
                "url": "https://www.minqin.gov.cn/col/col4098/index.html",
                "page_number": 1,
            },
            # 农村面源污染防治
            {
                "url": "https://www.minqin.gov.cn/col/col4104/index.html",
                "page_number": 1,
            },
            # 决策草案意见征集
            {
                "url": "https://www.minqin.gov.cn/col/col30290/index.html",
                "page_number": 1,
            },
            # 决策草案意见反馈
            {
                "url": "https://www.minqin.gov.cn/col/col30291/index.html",
                "page_number": 1,
            },
            # 农业、林业、水利
            {
                "url": "https://www.minqin.gov.cn/col/col4121/index.html",
                "page_number": 1,
            },
            # 城乡建设、环境保护
            {
                "url": "https://www.minqin.gov.cn/col/col4124/index.html",
                "page_number": 1,
            },
            # 公安、安全、司法
            {
                "url": "https://www.minqin.gov.cn/col/col4127/index.html",
                "page_number": 1,
            },
            # 民政、扶贫、救灾
            {
                "url": "https://www.minqin.gov.cn/col/col4128/index.html",
                "page_number": 1,
            },
            # 工业、交通
            {
                "url": "https://www.minqin.gov.cn/col/col4122/index.html",
                "page_number": 1,
            },
            # 国民经济管理、国有资产管理
            {
                "url": "https://www.minqin.gov.cn/col/col4118/index.html",
                "page_number": 1,
            },
            # 国土资源、能源
            {
                "url": "https://www.minqin.gov.cn/col/col4120/index.html",
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
        """
        :param params: start_urls中的每一项数据;
        :return: 包含内容的url等; e.g.[{'url': 'xx', 'title': 'xx', 'pubTime': 'xx',...}]
        """
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        m = re.search(r'<datastore>(.*?)</datastore>', resp.text, re.S)
        script = m.group(1).replace('<![CDATA[', '').replace(']]>', '')

        soup = BeautifulSoup(script, "html.parser")
        rows = soup.select('li')

        for row in rows:
            a_tag = row.select_one('a')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.get('title')
            pubTime = row.select_one('span').get_text(strip=True)
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        """
        :param params: get_list中返回的每一项数据;
        :return: 由title, pubTime, url, content等key构建的dict数据类型;
        """
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div#Zoom')

        if pdf_iframe := content.select_one('iframe'):
            pdf_tag = soup.new_tag('a', href=pdf_iframe.get('src'), string="附件")
            content.append(pdf_tag)
            pdf_iframe.decompose()

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
