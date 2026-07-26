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
        hostname = hostname.lower()
        if hostname.startswith("www."):
            hostname = hostname[4:]
        return hostname

    if _is_attachment(url_a) or _is_attachment(url_b):
        return False

    domain_a = _get_domain(url_a)
    domain_b = _get_domain(url_b)
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
            # 农村产权项目
            {
                "url": "https://enshi.ovupre.com/list/1195.html",
                "page_number": 1,
                "t": 1,
            },
            # 非公资产项目
            {
                "url": "https://enshi.ovupre.com/list/1196.html",
                "page_number": 1,
                "t": 1,
            },
            # 农村产权结果公告
            {
                "url": "https://enshi.ovupre.com/list/1360.html?type=new",
                "page_number": 1,
                "t": 1,
            },
            # 通知公告
            {
                "url": "https://enshi.ovupre.com/list/1293.html",
                "page_number": 1,
                "t": 2,
            },
        )

        for p in payload_list:
            for index in range(1, p["page_number"] + 1):
                cls.start_urls.append(
                    {
                        "url": p["url"],
                        "t": p["t"],
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params["url"], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return ret_list

        soup = BeautifulSoup(resp.text, "html.parser")
        if params["t"] == 2:
            rows = soup.select("div.list_news_txt div.newstxt div.item")

            for row in rows:
                a_tag = row.select_one("a.block")
                if not a_tag:
                    continue

                url = urljoin(params["url"], a_tag.get("href"))
                if not is_same_origin_url(url, params["url"]):
                    continue

                title = row.select_one(".title").get_text(strip=True)
                year = row.select_one(".time .year").get_text(strip=True)
                month_day = row.select_one(".time .data").get_text(strip=True)
                pubTime = f"{year}-{month_day}"

                ret_list.append(
                    {
                        "url": url,
                        "title": title,
                        "pubTime": pubTime,
                    }
                )
        else:
            rows = soup.select("div.noticetablewrap tbody tr")

            for row in rows:
                tds = row.select("td")
                if len(tds) < 2:
                    continue

                a_tag = row.select_one("a")
                if not a_tag:
                    continue

                url = urljoin(params["url"], a_tag.get("href"))
                if not is_same_origin_url(url, params["url"]):
                    continue

                title = tds[1].get_text(strip=True)

                ret_list.append(
                    {
                        "url": url,
                        "title": title,
                        "pubTime": None,
                    }
                )

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params["url"], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        if params["title"] is None:
            params["title"] = soup.select_one(".contTitle").get_text(strip=True)

        if params["pubTime"] is None:
            pub_time = soup.select_one(".contleft .time span").get_text(strip=True)
            params["pubTime"] = handle_str.extract_and_validate_dates(pub_time)[0]

        content = soup.select_one(".contBox")
        content = handle_str.completion_url(str(content), params["url"])

        return {
            "title": params["title"],
            "pubTime": params["pubTime"],
            "url": params["url"],
            "content": content,
        }


if __name__ == "__main__":
    CrawlerObject().start()
