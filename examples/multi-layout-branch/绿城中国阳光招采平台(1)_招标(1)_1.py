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
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": "https://lczc.gtcloud.cn",
    "Pragma": "no-cache",
    "Referer": "https://lczc.gtcloud.cn/portal/biding",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "isOut": "supplier",
    "reqmethod": "L3N1cHBsaWVycy9hbm5vdW5jZW1lbnQvZ2V0QW5ub3VuY2VtZW50",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "signature": "899c299a9a17b2fdd7f2bb9f43672195",
    "timestamp": "1782805509680"
}
COOKIES = {
    "_pk_id.1138.1888": "84daeb2a4229f968.1782805010."
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
            # 通知公告
            {
                "url": "https://lczc.gtcloud.cn/suppliers/announcement/getAnnouncement",
                "page_number": 10,
                'data': {
                    "title": None,
                    "start": None,
                    "end": None,
                    "regionIds": [],
                    "categoryIds": [],
                    "pageSize": 15,
                    "pageNumber": 5
                },
                't': 1
            },
            # 中标公告
            {
                "url": "https://lczc.gtcloud.cn/suppliers/bidWinLetter/getWinnerBidInfo?t=1782806595&page.size=15&page.page={}",
                "page_number": 2,
                'data': {},
                't': 2
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                if p['data']:
                    p['data']['pageNumber'] = index
                    cls.start_urls.append(
                        {
                            'url': p['url'], 'data': p['data'].copy(), 't': p['t']
                        }
                    )
                else:
                    cls.start_urls.append(
                        {
                            'url': p['url'].format(index), 't': p['t']
                        }
                    )

    def get_list(self, params: dict):
        ret_list = []

        if params['t'] == 1:
            resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, json=params['data'])
        else:
            resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)

        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('result').get('content') or resp.json().get('result').get('records')

        if params['t'] == 1:
            for row in rows:
                id = row.get('id')
                url = f"https://lczc.gtcloud.cn/announcementView?id={id}"

                title = row.get('title')
                pubTime = row.get('releaseTime')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id})
        if params['t'] == 2:
            for row in rows:
                id = row.get('id')
                url = f"https://lczc.gtcloud.cn/portal/win-biding?id={id}"

                title = row.get('cgPlanName')
                pubTime = row.get('createTime')

                content = f"""
                <p>中标公告名称：{title}</p>
                <p>中标单位: {row.get('supplierName')}</p>
                <p>发布时间: {pubTime}</p>
                """
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 'content': content})

        return ret_list

    def get_content(self, params: dict):
        if params.get('content'):
            return params

        url = f"https://lczc.gtcloud.cn/suppliers/announcement/getBidAnnouncement?t=1782805789&id={params['id']}"
        resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        obj = resp.json().get('result')
        content = self.render_content(obj)
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}

    def render_content(self, data):
        content = f"""
        <div>
        	<div>
        		<div><mark>招标公告</mark>名称：</div>
        		<div>{data.get('title', '')}</div>
        	</div>
        	<div>
        		<div><mark>招标</mark>主体：</div>
        		<div>{data.get('tenderParty', '')}</div>
        	</div>
        	<div>
        		<div>项目名称：</div>
        		<div>{data.get('projectName', '')}</div>
        		<div>发布时间：</div>
        		<div>{data.get('releaseTime', '')}</div>
        	</div>
        	<div>
        		<div><mark>招标</mark>适用范围：</div>
        		<div>{data.get('tenderScope', '')}</div>
        		<div>预计金额（元）：</div>
        		<div>{data.get('estimatedAmount', '')}</div>
        	</div>
        	<div>
        		<div>联系人：</div>
        		<div>{data.get('contact', '')}</div>
        		<div>联系电话：</div>
        		<div>{data.get('phone', '')}</div>
        	</div>
        	<div>
        		<div>专业品类：</div>
        		<div>
        			<div>{data.get('supplierCategoryName', '')}</div>
        		</div>
        	</div>
        	<div>
        		<div><mark>招标</mark>内容：</div>
        		<div>
        			<div>{data.get('announcementContent', '')}</div>
        		</div>
        	</div>
        	<div>
        		<div>报名开始时间：</div>
        		<div>{data.get('createTime', '')}</div>
        		<div>报名截止时间：</div>
        		<div>{data.get('deadLine', '')}</div>
        	</div>
        </div>
            """
        return content


if __name__ == "__main__":
    CrawlerObject().start()
