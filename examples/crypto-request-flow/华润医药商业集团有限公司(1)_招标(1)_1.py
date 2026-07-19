# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import re
import json
import subprocess
import sys
from bbSpider.agent_pool import agent_pool

sys.stdout.reconfigure(encoding="utf-8")


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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
COOKIES = {}


def get_cookie(url, proxies):
    for _ in range(3):
        resp = request.get(url, headers=HEADERS, timeout=20, proxies=proxies)
        if resp.status_code != 200:
            continue

        html = resp.text

        if "window.solveChallenge" in html:
            script = re.search(r"<script>(.*?)</script>", html, re.S | re.I).group(1)
            node_code = f"""
        const vm = require('vm');
        const ctx = {{
          window: {{}},
          document: {{ cookie: '' }},
          location: {{ href: 'https://www.crpcg.com/notice_news/index.html' }},
          console: console,
          Date: Date,
          Math: Math,
          setTimeout: setTimeout,
          clearTimeout: clearTimeout,
          navigator: {{ userAgent: {json.dumps(HEADERS["User-Agent"])} }},
        }};
        ctx.window = ctx;
        ctx.globalThis = ctx;
        ctx.location.replace = function (s) {{ this.href = s; }};
        vm.runInNewContext({json.dumps(script)}, ctx, {{ timeout: 5000 }});
        process.stdout.write(ctx.document.cookie);
        """
            cookie = subprocess.run(
                ["node", "-e", node_code],
                capture_output=True,
                text=True,
                timeout=20,
            ).stdout.strip()

            return cookie
    else:
        return None


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
                "url": "https://www.crpcg.com/notice_news/index.html",
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

        proxies = agent_pool(params['url'])[urlparse(params['url']).scheme]
        cookie = get_cookie(params['url'], proxies)
        if cookie is None:
            return ret_list

        resp = auto_request(url=params['url'], headers={**HEADERS, "Cookie": cookie}, proxies=proxies)
        if 400 <= resp.status_code <= 599:
            return ret_list

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select('div.ejNewsBox > div.item')

        for row in rows:
            a_tag = row.select_one('a')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.select_one('.title').get_text(strip=True)
            pubTime = row.select_one('.mTime').get_text(strip=True)
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        proxies = agent_pool(params['url'])[urlparse(params['url']).scheme]
        cookie = get_cookie(params['url'], proxies)
        if cookie is None:
            return None

        resp = auto_request(url=params['url'], headers={**HEADERS, "Cookie": cookie}, proxies=proxies)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('div.RCMS_EDITOR')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
