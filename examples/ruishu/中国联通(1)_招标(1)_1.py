# -*- coding: utf-8 -*-
import copy

import execjs
from bs4 import BeautifulSoup

from bbSpider import Spider, handle_str
from bbSpider import request
from bbSpider.utils import acquire_subjoin_path
from urllib.parse import urljoin

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/json;charset=UTF-8",
    "EXTRANET_COMPANY_REGISTER": "true",
    "Origin": "https://www.cuecp.cn",
    "Pragma": "no-cache",
    "Referer": "https://www.cuecp.cn/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "isIndex": "true",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "source": "extranet"
}


def get_cookies():
    for _ in range(8):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        }

        url = "https://www.cuecp.cn/"
        response = request.get(url, headers=headers, verify=False, proxy_safety='https')

        cookies = dict(response.cookies)

        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.select_one('meta[id][content]').get('content')

        code = soup.select_one('script').text

        tag = soup.select_one('head script[src]')
        domain_url = urljoin(url, tag.get('src'))
        resp = request.get(domain_url, headers=headers, proxy_safety="https")
        if resp.status_code != 200:
            continue

        domain = resp.text

        with open(acquire_subjoin_path('中国联通1.js'), 'rt', encoding='utf-8') as f:
            js_code = f.read()

        output = execjs.compile(js_code).call('general_cookie', content, code, domain)

        cookies.update(output)
        return cookies
    else:
        return None


class CrawlerObject(Spider):
    start_urls = []

    data_category = 1
    filter_type = "url"
    is_upload_data = 1
    collect_thread_number = 2

    @classmethod
    def init_func(cls):

        payload_list = (
            # 采购准备
            {"url": "https://www.cuecp.cn/app/api/index/noticeDetail",
             "data": {
                 'page': 1,
                 'size': 10,
                 'noticeType': "采购准备",
                 'noticeTitle': '',
                 'noticeGroup': 'PUR',
                 'startTime': '',
                 'endTime': '',
             },
             "t": 1,
             "page_number": 1,
             "data_category": 0},

            # 采购公告
            {"url": "https://www.cuecp.cn/app/api/index/noticeDetail",
             "data": {
                 'page': 1,
                 'size': 10,
                 'noticeType': "采购公告",
                 'noticeTitle': '',
                 'noticeGroup': 'PUR',
                 'startTime': '',
                 'endTime': '',
             },
             "t": 1,
             "page_number": 15,
             "data_category": 0},

            # 采购结果
            {"url": "https://www.cuecp.cn/app/api/index/noticeDetail",
             "data": {
                 'page': 1,
                 'size': 10,
                 'noticeType': "采购结果",
                 'noticeTitle': '',
                 'noticeGroup': 'PUR',
                 'startTime': '',
                 'endTime': '',
             },
             "t": 1,
             "page_number": 5,
             "data_category": 0},

            # 国际供应商服务平台
            # 招标公告
            {"url": "https://www.cuecp.cn/app/api/index/findInNoticeMsg/1/10",
             "data": {
                 "noticeTitle": "",
                 "startTime": "",
                 "attribute6": "",
                 "attribute7": "",
                 "noticeType": "招标公告"
             },
             "t": 2,
             "page_number": 1,
             "data_category": 0},

            # 中标候选人公示
            {"url": "https://www.cuecp.cn/app/api/index/findInNoticeMsg/1/10",
             "data": {
                 "noticeTitle": "",
                 "startTime": "",
                 "attribute6": "",
                 "attribute7": "",
                 "noticeType": "中标候选人公示"
             },
             "t": 2,
             "page_number": 1,
             "data_category": 0},

            # 需求公示
            {"url": "https://www.cuecp.cn/app/api/index/findInNoticeMsg/1/10",
             "data": {
                 "noticeTitle": "",
                 "startTime": "",
                 "attribute6": "",
                 "attribute7": "",
                 "noticeType": "需求公示"
             },
             "t": 2,
             "page_number": 1,
             "data_category": 0},

        )
        for item in payload_list:
            for i in range(1, item['page_number'] + 1):
                if item['t'] == 1:
                    item['data']['page'] = i
                cls.start_urls.append(
                    {"url": item["url"].format(i), "data": copy.deepcopy(item['data']), "data_category": item["data_category"], "t": item['t']})

    def get_list(self, params):
        result = []

        cookies = get_cookies()
        if cookies is None:
            return result

        if params['t'] == 1:
            response = request.post(params['url'], headers=headers, cookies=cookies, json=params['data'], proxy_safety='https')
            if 400 <= response.status_code <= 599:
                return result

            row = response.json().get('data').get('purBeansInfoPage').get('list')
            for i in row:
                id = i["id"]
                page_url = f'https://www.cuecp.cn/#/register/Supplierannouncement/#/{i["id"]}'
                title = i['noticeTitle']
                publish_time = i['createDate']
                publish_time = handle_str.extract_and_validate_dates(publish_time)[0]
                noticeGroup = i['noticeGroup']
                result.append(
                    {"title": title, "url": page_url, "pubTime": publish_time, "t": params['t'], "id": id,
                     "noticeGroup": noticeGroup})
        if params['t'] == 2:
            response = request.post(params['url'], headers=headers, cookies=cookies, json=params['data'], proxy_safety='https')
            if 400 <= response.status_code <= 599:
                return result

            row = response.json().get('data').get('list')
            for i in row:
                id = i['id']
                noticeCode = i['noticeCode']
                noticeGroup = i['noticeGroup']
                page_url = f"https://www.cuecp.cn/#/register/IntSupplyPlatLookDetailPage?attachlist=&id={id}&noticeGroup={noticeGroup}&noticeCode={noticeCode}"

                title = i['noticeTitle']
                publish_time = i['startTime']
                result.append(
                    {"title": title, "url": page_url, "pubTime": publish_time, "t": params['t'], "id": id,
                     "noticeGroup": noticeGroup})

        return result

    def get_content(self, params):
        """
        Attachment 附件
        Body 内容
        """
        cookies = get_cookies()
        if cookies is None:
            return None

        url = "https://www.cuecp.cn/app/api/index/noticeDetail"
        json_data = {
            'page': 1,
            'size': 10,
            'noticeGroup': params['noticeGroup'],
            'id': params['id'],
        }
        response = request.post(url, headers=headers, cookies=cookies, json=json_data, proxy_safety='https')
        if 400 <= response.status_code <= 599:
            return None

        data = response.json().get('data')
        content = data['noticeText']

        if attachFileList := data.get('attachFileList'):
            for item in attachFileList:
                href = f"https://www.cuecp.cn/app/common/file/download/{item.get('fileUuid')}"
                a_tag = f'<a href="{href}">{item.get("fileName")}</a>'
                content += a_tag

        content = handle_str.completion_url(str(content), params['url'])

        return {'title': params['title'], 'pubTime': params['pubTime'], 'url': params['url'], 'content': content}


if __name__ == '__main__':
    CrawlerObject().start()
