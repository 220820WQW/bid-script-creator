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
            # 信息公开
            {
                "url": "http://nxzxyjhyy.com/prod-api/cms/open-api/selectArticleListByColumnId/20",
                "page_number": 1,
                "data": {
                    "columnId": 20,
                    "pageSize": 5,
                    "pageNum": 1,
                }
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                data = p['data'].copy()
                data['pageNum'] = index
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': data
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], params=params['data'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('rows')

        for row in rows:
            article_id = row.get('articleId')
            url = urljoin(
                'http://nxzxyjhyy.com/tp1?_t=1784030949173&itemId=20&type=1',
                f"/tp1/detail?itemId={article_id}&type=0"
            )
            if not is_same_origin_url(url, 'http://nxzxyjhyy.com/tp1?_t=1784030949173&itemId=20&type=1'):
                continue

            title = row.get('title')
            pubTime = row.get('publishTime')
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'articleId': article_id})

        return ret_list

    def get_content(self, params: dict):
        detail_url = f"http://nxzxyjhyy.com/prod-api/cms/open-api/getArticle/{params['articleId']}"
        resp = auto_request(url=detail_url, headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        data = resp.json().get('data')
        content = data.get('content')

        asset_url = f"http://nxzxyjhyy.com/prod-api/cms/open-api/selectAssetByRefId/{params['articleId']}"
        asset_resp = auto_request(url=asset_url, headers=HEADERS, cookies=COOKIES)
        if 400 <= asset_resp.status_code <= 599:
            return None

        attachments = asset_resp.json().get('data')
        if attachments:
            soup = BeautifulSoup(content, "html.parser")
            for attachment in attachments:
                assets_url = attachment.get('assetsUrl')
                if not assets_url:
                    continue
                a_tag = soup.new_tag(
                    'a',
                    href=urljoin(params['url'], f"/prod-api{assets_url}"),
                    string=attachment.get('assetsName')
                )
                soup.append(a_tag)
                soup.append(soup.new_tag('br'))
            content = str(soup)

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
