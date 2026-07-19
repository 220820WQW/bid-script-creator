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
            #  重点领域
            {
                "url": "https://www.shanzhou.gov.cn/18048/0000/zhengfuxinxi-1.html",
                "page_number": 1,
                't': 1
            },
            #  公告公示
            {
                "url": "https://www.shanzhou.gov.cn/18019/0000/zhengfuxinxi-1.html",
                "page_number": 1,
                't': 1
            },
            #  建议提案办理
            {
                "url": "https://www.shanzhou.gov.cn/18108/0000/zhengfuxinxi-1.html",
                "page_number": 1,
                't': 1
            },
            #  征集结果反馈
            {
                "url": "https://www.shanzhou.gov.cn/18227/0000/list-1.html",
                "page_number": 1,
                't': 1
            },
            #  乡村振兴战略
            {
                "url": "https://www.shanzhou.gov.cn/18292/0000/zhengfuxinxi-1.html",
                "page_number": 1,
                't': 1
            },

            #  重点领域公开
            # 批准服务
            {
                "url": "https://www.shanzhou.gov.cn/19195/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },
            # 重点项目遴选
            {
                "url": "https://www.shanzhou.gov.cn/19225/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },

            # 义务教育 通知公告
            {
                "url": "https://www.shanzhou.gov.cn/18215/0000/subList-1.html",
                "page_number": 1,
                't': 1
            },
            # 涉农补贴 公示公告
            {
                "url": "https://www.shanzhou.gov.cn/18173/0000/subList-1.html",
                "page_number": 1,
                't': 1
            },
            # 公共文化服务  公示公告
            {
                "url": "https://www.shanzhou.gov.cn/18399/0000/subList-1.html",
                "page_number": 1,
                't': 1
            },
            # 生态环境 通知公告
            {
                "url": "https://www.shanzhou.gov.cn/18141/0000/subList-1.html",
                "page_number": 1,
                't': 1
            },
            # 生态环境 受理和拟审批信息公开
            {
                "url": "https://www.shanzhou.gov.cn/18078/0000/subList-1.html",
                "page_number": 1,
                't': 1
            },
            # 生态环境 项目批复公开
            {
                "url": "https://www.shanzhou.gov.cn/18080/0000/subList-1.html",
                "page_number": 1,
                't': 2
            },

            # 国有土地上房屋征收与补偿领域 国家层面法规政策
            {
                "url": "https://www.shanzhou.gov.cn/20752/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },
            # 国有土地上房屋征收与补偿领域 地方层面法规政策
            {
                "url": "https://www.shanzhou.gov.cn/20755/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },
            # 国有土地上房屋征收与补偿领域 房屋征收决定公告
            {
                "url": "https://www.shanzhou.gov.cn/20758/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },

            # 财政预决算 公示公告
            {
                "url": "https://www.shanzhou.gov.cn/18213/0000/subList-1.html",
                "page_number": 1,
                't': 1
            },

            # 卫生健康 通知公告
            {
                "url": "https://www.shanzhou.gov.cn/21013/0000/subList-1.html",
                "page_number": 1,
                't': 1
            },
            # 安全生产 公示公告
            {
                "url": "https://www.shanzhou.gov.cn/18168/0000/subList-1.html",
                "page_number": 1,
                't': 1
            },

            # 自然资源
            # 土地供应计划
            {
                "url": "https://www.shanzhou.gov.cn/20272/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },
            # 土地出让公告
            {
                "url": "https://www.shanzhou.gov.cn/20275/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },
            # 土地出让结果
            {
                "url": "https://www.shanzhou.gov.cn/20278/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },
            # 闲置土地
            {
                "url": "https://www.shanzhou.gov.cn/20287/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },
            # 县级国土空间总体规划
            {
                "url": "https://www.shanzhou.gov.cn/20263/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },
            # 详细规划
            {
                "url": "https://www.shanzhou.gov.cn/20266/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },
            # 专项规划
            {
                "url": "https://www.shanzhou.gov.cn/20269/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },
            # 生态修复项目批准
            {
                "url": "https://www.shanzhou.gov.cn/20050/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },
            # 农村集体经济组织兴办企业用地审核
            {
                "url": "https://www.shanzhou.gov.cn/20242/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },
            # 乡（镇）村公共设施、公益事业建设用地审核
            {
                "url": "https://www.shanzhou.gov.cn/20245/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },
            # 临时用地审批
            {
                "url": "https://www.shanzhou.gov.cn/20248/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },
            # 开采矿产资源审批
            {
                "url": "https://www.shanzhou.gov.cn/20086/0000/jczwgkList-1.html",
                "page_number": 1,
                't': 2
            },

            # 救灾 公示公告
            {
                "url": "https://www.shanzhou.gov.cn/18168/0000/subList-1.html",
                "page_number": 1,
                't': 1
            },

            # 扶贫 公示公告
            {
                "url": "https://www.shanzhou.gov.cn/18173/0000/subList-1.html",
                "page_number": 1,
                't': 1
            },
            # 旅游 公示公告
            {
                "url": "https://www.shanzhou.gov.cn/18399/0000/subList-1.html",
                "page_number": 1,
                't': 1
            },

            # 水利
            {
                "url": "https://www.shanzhou.gov.cn/19216/0000/jczwgkmoreList-1.html",
                "page_number": 1,
                't': 2
            },

            #  规划信息
            {
                "url": "https://www.shanzhou.gov.cn/18309/0000/zhengfuxinxi-1.html",
                "page_number": 1,
                't': 1
            },
            #  复议决定公开
            {
                "url": "https://www.shanzhou.gov.cn/26062/0000/zhengfuxinxi-1.html",
                "page_number": 1,
                't': 1
            },
            #  应急预案
            {
                "url": "https://www.shanzhou.gov.cn/21988/0000/zhengfuxinxi-1.html",
                "page_number": 1,
                't': 1
            },
            #  双随机、一公开
            {
                "url": "https://www.shanzhou.gov.cn/28795/0000/zhengfuxinxi-1.html",
                "page_number": 1,
                't': 1
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
            rows = soup.select('div.article-list ul li') or soup.select('.category_r_list ul li')

            for row in rows:
                a_tag = row.select_one('a')
                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                title = a_tag.select_one('.qians, .list-name').get_text(strip=True)
                pubTime = row.select_one('.hous, .more_right').get_text(strip=True)
                pubTime = handle_str.extract_and_validate_dates(pubTime)[0]
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})
        if params['t'] == 2:
            rows = soup.select('div.article-container ul li')

            for row in rows:
                a_tag = row.select_one('a')
                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                title = a_tag.select_one('.article-name').get_text(strip=True)
                pubTime = row.select_one('a > .info-container:last-child').get_text(strip=True)
                pubTime = handle_str.extract_and_validate_dates(pubTime)[0]
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div#content')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
