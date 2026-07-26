# -*- coding: UTF-8 -*-
import json
import re
import subprocess
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
from bbSpider.agent_pool import agent_pool


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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://wlj.hefei.gov.cn/",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
    "Sec-CH-UA": '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
}
COOKIES = {}


def solve_first_cookie(challenge_html: str) -> str:
    match = re.search(r"document\.cookie=(.+?);location\.href", challenge_html)
    if not match:
        raise RuntimeError("first challenge not found")
    expr = match.group(1)
    return subprocess.check_output(
        ["node", "-e", f"console.log(eval({json.dumps(expr)}))"],
        text=True,
        encoding="utf-8",
    ).strip().split(";", 1)[0]


def solve_second_cookie(challenge_html: str) -> str:
    scripts = re.findall(r"<script>(.*?)</script>", challenge_html, re.S)
    if not scripts:
        raise RuntimeError("second challenge script not found")
    script_text = scripts[-1]
    node_code = r"""
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync(0, 'utf8');
let cookie = '';
const document = {
  documentElement: { style: { setProperty() {} } },
  head: { appendChild() {} },
  body: { appendChild() {} },
  createElement() { return { style: {}, appendChild() {}, setAttribute() {}, innerHTML: '' }; },
  getElementById() { return null; },
};
Object.defineProperty(document, 'cookie', {
  get() { return cookie; },
  set(v) { cookie = v; },
});
const context = {
  window: null,
  document,
  location: {
    protocol: 'https:',
    pathname: '/content/column/6789151',
    search: '?pageIndex=1',
    href: 'https://wjw.hefei.gov.cn/content/column/6789151?pageIndex=1',
  },
  navigator: {
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
    platform: 'Win32',
    language: 'zh-CN',
    languages: ['zh-CN', 'zh', 'en-US', 'en'],
    vendor: 'Google Inc.',
    webdriver: false,
  },
  screen: { width: 1920, height: 1080 },
  setTimeout,
  clearTimeout,
  console,
  Date,
  Math,
  Promise,
  URL,
  Blob,
  Worker: function () {},
  fetch: async () => ({ status: 404, text: async () => '', json: async () => ({}) }),
  atob: (s) => Buffer.from(s, 'base64').toString('binary'),
  btoa: (s) => Buffer.from(s, 'binary').toString('base64'),
};
context.window = context;
vm.createContext(context);
vm.runInContext(src, context, { timeout: 10000 });
setTimeout(() => console.log(cookie), 2600);
"""
    return subprocess.check_output(
        ["node", "-e", node_code],
        input=script_text,
        text=True,
        encoding="utf-8",
    ).strip().split(";", 1)[0]


def get_cookies(proxies=None):
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://wlj.hefei.gov.cn/",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
        "Sec-CH-UA": '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
    }

    url = "https://wlj.hefei.gov.cn/"
    first_response = request.get(url, headers=headers, timeout=30, proxies=proxies)
    cookies = first_response.cookies.get_dict()
    if not cookies:
        return None

    first_cookie = solve_first_cookie(first_response.text)
    k, v = first_cookie.split('=')
    cookies[k] = v

    second_response = request.get("https://wlj.hefei.gov.cn/", headers=headers, cookies=cookies, timeout=30, proxies=proxies)
    second_cookie = solve_second_cookie(second_response.text)
    k, v = second_cookie.split('=')
    cookies[k] = v

    if len(cookies) < 2:
        return None

    return cookies


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
                "url": "https://wlj.hefei.gov.cn/wldt/tzgg/index.html",
                "page_number": 1,
                't': 1
            },
            # 公告公示
            {
                "url": "https://wlj.hefei.gov.cn/wldt/gggs/index.html",
                "page_number": 1,
                't': 1
            },
            # 意见征集
            {
                "url": "https://wlj.hefei.gov.cn/mayor/site/label/8888?_=0.27716043020630443&labelName=publicInfoList&siteId=6784341&organId=20261&pageSize=10&pageIndex=1&isDate=true&dateFormat=yyyy-MM-dd&length=50&type=4&action=list&result=&isJson=true&isRel=true&catId=6996411",
                "page_number": 1,
                't': 2
            },
            # 意见反馈
            {
                "url": "https://wlj.hefei.gov.cn/mayor/site/label/8888?_=0.5658448363522834&labelName=publicInfoList&siteId=6784341&organId=20261&pageSize=10&pageIndex=1&isDate=true&dateFormat=yyyy-MM-dd&length=50&type=4&action=list&result=&isJson=true&isRel=true&catId=6996431",
                "page_number": 1,
                't': 2
            },
            # 行政权力运行结果
            {
                "url": "https://wlj.hefei.gov.cn/mayor/site/label/8888?_=0.26799597171189604&labelName=publicInfoList&siteId=6784341&organId=20261&pageSize=10&pageIndex=1&isDate=true&dateFormat=yyyy-MM-dd&length=50&type=4&action=list&result=&isJson=true&isRel=true&catId=7036330",
                "page_number": 1,
                't': 2
            },
            # 规划信息
            {
                "url": "https://wlj.hefei.gov.cn/mayor/site/label/8888?_=0.22517330601642294&labelName=publicInfoList&siteId=6784341&organId=20261&pageSize=20&pageIndex=1&isDate=true&dateFormat=yyyy-MM-dd&length=50&type=4&action=list&result=&isJson=true&keyWords=&isRel=true&catIds=&catId=7036378&excludeTitleContent=",
                "page_number": 1,
                't': 2
            },
            # 人大代表建议办理
            {
                "url": "https://wlj.hefei.gov.cn/mayor/site/label/8888?_=0.9528730174744517&labelName=publicInfoList&siteId=6784341&organId=20261&pageSize=10&pageIndex=1&isDate=true&dateFormat=yyyy-MM-dd&length=50&type=4&action=list&result=&isJson=true&isRel=true&catId=6721411",
                "page_number": 1,
                't': 2
            },
            # 政协提案办理
            {
                "url": "https://wlj.hefei.gov.cn/mayor/site/label/8888?_=0.2593136230156474&labelName=publicInfoList&siteId=6784341&organId=20261&pageSize=10&pageIndex=1&isDate=true&dateFormat=yyyy-MM-dd&length=50&type=4&action=list&result=&isJson=true&isRel=true&catId=6721421",
                "page_number": 1,
                't': 2
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

        for _ in range(8):
            try:
                proxies = agent_pool(params['url'])['http']
                cookies = get_cookies(proxies)
                if cookies:
                    break
            except:
                continue
        else:
            return ret_list

        cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        headers = HEADERS.copy()
        headers["Cookie"] = cookie_str

        resp = auto_request(url=params['url'], headers=headers, proxies=proxies)
        if 400 <= resp.status_code <= 599:
            return ret_list

        if params['t'] == 1:
            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.select('.doc_list li')

            for row in rows:
                a_tag = row.select_one('a')
                if not a_tag:
                    continue

                url = urljoin(params['url'], a_tag.get('href'))
                if not is_same_origin_url(url, params['url']):
                    continue

                title = a_tag.get_text(strip=True)
                pubTime = row.select_one('span.date').get_text(strip=True)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        if params['t'] == 2:
            rows = resp.json().get('data')

            for row in rows:
                url = row.get('link')
                if not is_same_origin_url(url, params['url']):
                    continue

                title = row.get('title')
                pubTime = row.get('publishDate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        for _ in range(8):
            try:
                proxies = agent_pool(params['url'])['http']
                cookies = get_cookies(proxies)
                if cookies:
                    break
            except:
                continue
        else:
            return None

        cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        headers = HEADERS.copy()
        headers["Cookie"] = cookie_str

        resp = auto_request(url=params['url'], headers=headers, proxies=proxies)
        if 400 <= resp.status_code <= 599:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one('#zoom')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
