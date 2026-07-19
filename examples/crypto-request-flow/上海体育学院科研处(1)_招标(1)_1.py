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

BASE64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="


def _build_reverse_dict(alphabet: str) -> dict[str, int]:
    return {ch: idx for idx, ch in enumerate(alphabet)}


def _get_base_value(reverse: dict[str, int], ch: str) -> int:
    return reverse[ch]


def lzstring_decompress_from_base64(data: str) -> str:
    """
    Python port of LZString.decompressFromBase64.

    The site payload is compatible with this variant. The implementation
    mirrors the JS bitstream decoder used by the page's `d(...)` function.
    """

    if data is None:
        return ""
    if data == "":
        return ""

    reverse = _build_reverse_dict(BASE64_ALPHABET)
    # The original page uses `_decprs(length, 32, callback)`.
    length = len(data)
    reset_value = 32

    def next_value(idx: int) -> int:
        return _get_base_value(reverse, data[idx])

    dictionary: dict[int, str] = {}
    enlarge_in = 4
    dict_size = 4
    num_bits = 3

    # Read first code (2 bits)
    data_state = {"val": next_value(0), "position": reset_value, "index": 1}
    bits = 0
    power = 1
    maxpower = 4
    while power != maxpower:
        resb = data_state["val"] & data_state["position"]
        data_state["position"] >>= 1
        if data_state["position"] == 0:
            data_state["position"] = reset_value
            if data_state["index"] < length:
                data_state["val"] = next_value(data_state["index"])
            data_state["index"] += 1
        if resb > 0:
            bits |= power
        power <<= 1

    c = bits
    if c == 0:
        bits = 0
        maxpower = 1 << 8
        power = 1
        while power != maxpower:
            resb = data_state["val"] & data_state["position"]
            data_state["position"] >>= 1
            if data_state["position"] == 0:
                data_state["position"] = reset_value
                if data_state["index"] < length:
                    data_state["val"] = next_value(data_state["index"])
                data_state["index"] += 1
            if resb > 0:
                bits |= power
            power <<= 1
        c = chr(bits)
    elif c == 1:
        bits = 0
        maxpower = 1 << 16
        power = 1
        while power != maxpower:
            resb = data_state["val"] & data_state["position"]
            data_state["position"] >>= 1
            if data_state["position"] == 0:
                data_state["position"] = reset_value
                if data_state["index"] < length:
                    data_state["val"] = next_value(data_state["index"])
                data_state["index"] += 1
            if resb > 0:
                bits |= power
            power <<= 1
        c = chr(bits)
    elif c == 2:
        return ""

    dictionary[3] = c
    w = c
    result = [c]

    while True:
        if data_state["index"] > length:
            return ""

        bits = 0
        maxpower = 1 << num_bits
        power = 1
        while power != maxpower:
            resb = data_state["val"] & data_state["position"]
            data_state["position"] >>= 1
            if data_state["position"] == 0:
                data_state["position"] = reset_value
                if data_state["index"] < length:
                    data_state["val"] = next_value(data_state["index"])
                data_state["index"] += 1
            if resb > 0:
                bits |= power
            power <<= 1

        c = bits

        if c == 0:
            bits = 0
            maxpower = 1 << 8
            power = 1
            while power != maxpower:
                resb = data_state["val"] & data_state["position"]
                data_state["position"] >>= 1
                if data_state["position"] == 0:
                    data_state["position"] = reset_value
                    if data_state["index"] < length:
                        data_state["val"] = next_value(data_state["index"])
                    data_state["index"] += 1
                if resb > 0:
                    bits |= power
                power <<= 1
            dictionary[dict_size] = chr(bits)
            c = dict_size
            dict_size += 1
            enlarge_in -= 1
        elif c == 1:
            bits = 0
            maxpower = 1 << 16
            power = 1
            while power != maxpower:
                resb = data_state["val"] & data_state["position"]
                data_state["position"] >>= 1
                if data_state["position"] == 0:
                    data_state["position"] = reset_value
                    if data_state["index"] < length:
                        data_state["val"] = next_value(data_state["index"])
                    data_state["index"] += 1
                if resb > 0:
                    bits |= power
                power <<= 1
            dictionary[dict_size] = chr(bits)
            c = dict_size
            dict_size += 1
            enlarge_in -= 1
        elif c == 2:
            return "".join(result)

        if enlarge_in == 0:
            enlarge_in = 1 << num_bits
            num_bits += 1

        if c in dictionary:
            entry = dictionary[c]
        elif c == dict_size:
            entry = w + w[0]
        else:
            return ""

        result.append(entry)

        dictionary[dict_size] = w + entry[0]
        dict_size += 1
        enlarge_in -= 1
        w = entry

        if enlarge_in == 0:
            enlarge_in = 1 << num_bits
            num_bits += 1


def decode_d_payload(o: str, p: str = "3", y: str = "x", z: str = "10", f: str = "0", m: str = "") -> str:
    """
    Offline equivalent for the page's `d(o,p,y,z,f,m)`.

    The page's wrapper uses `p/y/z/f/m` as obfuscated parameters and
    a webdriver gate. In practice, the decoded content is determined by `o`.
    The extra parameters are accepted for compatibility and traceability.
    """
    _ = (p, y, z, f, m)
    return lzstring_decompress_from_base64(o)


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 公示信息
            {
                "url": "https://kyc.sus.edu.cn/gsxx.htm",
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

        m = re.search(r"var o='(.*?)';", resp.text)
        html = decode_d_payload(m.group(1))
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select('div.newlist > ul li')

        for row in rows:
            a_tag = row.select_one('a')
            url = urljoin(params['url'], a_tag.get('href'))
            if not is_same_origin_url(url, params['url']):
                continue

            title = a_tag.select_one('h1').get_text(strip=True)
            pubTime = row.select_one('.date').get_text(strip=True)
            ret_list.append({'url': url, 'title': title, 'pubTime': pubTime})

        return ret_list

    def get_content(self, params: dict):
        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        if 400 <= resp.status_code <= 599:
            return None

        m = re.search(r"var o='(.*?)';", resp.text)
        html = decode_d_payload(m.group(1))
        soup = BeautifulSoup(html, "html.parser")
        content = soup.select_one('div.v_news_content')
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
