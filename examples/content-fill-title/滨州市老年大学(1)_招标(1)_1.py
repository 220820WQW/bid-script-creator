# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str


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
        return hostname.lower().removeprefix("www.")

    if _is_attachment(url_a) or _is_attachment(url_b):
        return False

    return _get_domain(url_a) == _get_domain(url_b)


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
            # 网站公告
            {
                "url": "http://www.bzslndx.cn/list.php?fid=4",
                "page_number": 1,
            },
        )

        for p in payload_list:
            for index in range(1, p["page_number"] + 1):
                cls.start_urls.append(
                    {
                        "url": p["url"] if index == 1 else f"{p['url']}&page={index}",
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params["url"], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("table#list_article tr")

        for row in rows:
            a_tag = row.select_one('a[href*="bencandy.php?fid=4&id="]')
            if not a_tag:
                continue

            url = urljoin(params["url"], a_tag.get("href"))
            if not is_same_origin_url(url, params["url"]):
                continue

            pub_text = row.select_one('span[style*="float:right"]').get_text(strip=True)
            pubTime = handle_str.extract_and_validate_dates(pub_text)[0]

            ret_list.append(
                {
                    "url": url,
                    "title": None,
                    "pubTime": pubTime,
                }
            )

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params["url"], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        if params["title"] is None:
            params["title"] = soup.select_one("div.main_title").get_text(strip=True)

        if params["pubTime"] is None:
            pub_text = soup.select_one("div.top_about").get_text(" ", strip=True)
            params["pubTime"] = handle_str.extract_and_validate_dates(pub_text)[0]

        content = soup.select_one("div.content")
        content = handle_str.completion_url(str(content), params["url"])

        return {
            "title": params["title"],
            "pubTime": params["pubTime"],
            "url": params["url"],
            "content": content,
        }


if __name__ == "__main__":
    CrawlerObject().start()
