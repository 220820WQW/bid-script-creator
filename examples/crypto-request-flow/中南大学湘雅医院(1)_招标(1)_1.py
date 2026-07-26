# -*- coding: UTF-8 -*-
import base64
import time
from urllib.parse import urlparse

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
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
    "Origin": "https://xiangya.51eliao.com",
    "Pragma": "no-cache",
    "Referer": "https://xiangya.51eliao.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
COOKIES = {}

KEY = b'!@QE^%^WE51ElIaO'  # 16 bytes
IV = b'9693951890523540'  # 16 bytes


def aes_cbc_decrypt_b64(cipher_text_b64: str, key: bytes = KEY, iv: bytes = IV) -> str:
    """
    解密前端 Pa() 同款 AES-CBC 字符串
    :param cipher_text_b64: base64 编码的密文
    :return: 解密后的明文字符串
    """
    cipher_bytes = base64.b64decode(cipher_text_b64)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plain_padded = cipher.decrypt(cipher_bytes)
    plain = unpad(plain_padded, AES.block_size)
    return plain.decode("utf-8")


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 采购公告 院内采购
            {
                "url": "https://anno.51eliao.com/hospital/site/selectAllPortalMpProjectOneHbplatList.do",
                "page_number": 1,
                'data': {
                    "pageNum": "1",
                    "pageSize": "15",
                    "startTime": "",
                    "endTime": "",
                    "noticeTitle": "",
                    "siteDomainName": "xiangya",
                    "getDataTime": "1784728956945"
                },
                't': 1
            },
            # 采购公告 耗材试剂
            {
                "url": "https://anno.51eliao.com/hospital/site/selectAllPortalMpProjectOneConsumablesList.do",
                "page_number": 1,
                'data': {
                    "pageNum": "1",
                    "pageSize": "15",
                    "startTime": "",
                    "endTime": "",
                    "noticeTitle": "",
                    "siteDomainName": "xiangya",
                    "getDataTime": "1784728956945"
                },
                't': 2
            },

            # 采购公告变更 院内采购
            {
                "url": "https://anno.51eliao.com/hospital/site/selectAllPortalMpProjectChangeHbplatList.do",
                "page_number": 1,
                'data': {
                    "pageNum": "1",
                    "pageSize": "15",
                    "startTime": "",
                    "endTime": "",
                    "noticeTitle": "",
                    "siteDomainName": "xiangya",
                    "getDataTime": "1784728956945"
                },
                't': 3
            },
            # 采购公告变更 耗材试剂
            {
                "url": "https://anno.51eliao.com/hospital/site/selectAllPortalMpProjectChangeConsumablesList.do",
                "page_number": 1,
                'data': {
                    "pageNum": "1",
                    "pageSize": "15",
                    "startTime": "",
                    "endTime": "",
                    "noticeTitle": "",
                    "siteDomainName": "xiangya",
                    "getDataTime": "1784728956945"
                },
                't': 4
            },

            # 采购结果公示 院内采购
            {
                "url": "https://anno.51eliao.com/hospital/site/selectAllPortalAnnouncementHbplatList.do",
                "page_number": 1,
                'data': {
                    "pageNum": "1",
                    "pageSize": "15",
                    "startTime": "",
                    "endTime": "",
                    "noticeTitle": "",
                    "siteDomainName": "xiangya",
                    "getDataTime": "1784728956945"
                },
                't': 5
            },
            # 采购结果公示 耗材试剂
            {
                "url": "https://anno.51eliao.com/hospital/site/selectAllPortalAnnouncementConsumablesList.do",
                "page_number": 1,
                'data': {
                    "pageNum": "1",
                    "pageSize": "15",
                    "startTime": "",
                    "endTime": "",
                    "noticeTitle": "",
                    "siteDomainName": "xiangya",
                    "getDataTime": "1784728956945"
                },
                't': 6
            },

        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                p['data']['pageNum'] = str(index)
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy(), 't': p['t']
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, params=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        rows = resp.json().get('data').get('list')

        if params['t'] == 1:
            url_map = {
                1: "https://xiangya.51eliao.com/#/web/purchaserWeb/projectNoticeDetail/{}/2"
            }
            for row in rows:
                id_raw = row.get('id')
                id = aes_cbc_decrypt_b64(id_raw) if isinstance(id_raw, str) else id_raw
                beToType = row.get('beToType')
                url = url_map[beToType].format(id)

                title = row.get('noticeTitle')
                pubTime = row.get('publishDate')

                mpProjectId = row.get('mpProjectId')
                mpProjectId = aes_cbc_decrypt_b64(mpProjectId) if isinstance(mpProjectId, str) else mpProjectId
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'mpProjectId': mpProjectId, 'id': id, 'beToType': beToType, 't': params['t']})

        if params['t'] == 2:
            url_map = {
                1: "https://xiangya.51eliao.com/#/web/purchaserWeb/consumableProjectNoticeDetail/{}/2"
            }
            for row in rows:
                id_raw = row.get('id')
                id = aes_cbc_decrypt_b64(id_raw) if isinstance(id_raw, str) else id_raw
                beToType = row.get('beToType')
                url = url_map[beToType].format(id)

                title = row.get('noticeTitle')
                pubTime = row.get('publishDate')

                mpProjectId = row.get('mpProjectId')
                mpProjectId = aes_cbc_decrypt_b64(mpProjectId) if isinstance(mpProjectId, str) else mpProjectId
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'mpProjectId': mpProjectId, 'id': id, 'beToType': beToType, 't': params['t']})

        if params['t'] == 3:
            url_map = {
                2: "https://xiangya.51eliao.com/#/web/purchaserWeb/projectNoticeDetail/{}/1",
                11: "https://xiangya.51eliao.com/#/web/purchaserWeb/recallProjectNoticeDetail/{}"
            }
            for row in rows:
                id_raw = row.get('id')
                id = aes_cbc_decrypt_b64(id_raw) if isinstance(id_raw, str) else id_raw
                beToType = row.get('beToType')
                url = url_map[beToType].format(id)

                title = row.get('noticeTitle')
                pubTime = row.get('publishDate')

                mpProjectId = row.get('mpProjectId')
                mpProjectId = aes_cbc_decrypt_b64(mpProjectId) if isinstance(mpProjectId, str) else mpProjectId
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'mpProjectId': mpProjectId, 'id': id, 'beToType': beToType, 't': params['t']})

        if params['t'] == 4:
            url_map = {
                2: "https://xiangya.51eliao.com/#/web/purchaserWeb/consumableProjectNoticeDetail/{}/1"
            }
            for row in rows:
                id_raw = row.get('id')
                id = aes_cbc_decrypt_b64(id_raw) if isinstance(id_raw, str) else id_raw
                beToType = row.get('beToType')
                url = url_map[beToType].format(id)

                title = row.get('noticeTitle')
                pubTime = row.get('publishDate')

                mpProjectId = row.get('mpProjectId')
                mpProjectId = aes_cbc_decrypt_b64(mpProjectId) if isinstance(mpProjectId, str) else mpProjectId
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'mpProjectId': mpProjectId, 'id': id, 'beToType': beToType, 't': params['t']})

        if params['t'] == 5:
            url_map = {
                1: "https://xiangya.51eliao.com/#/web/purchaserWeb/projectResultNoticeDetail/{}/2",
                2: "https://xiangya.51eliao.com/#/web/purchaserWeb/projectResultNoticeDetail/{}/2"
            }
            for row in rows:
                id_raw = row.get('id')
                id = aes_cbc_decrypt_b64(id_raw) if isinstance(id_raw, str) else id_raw
                beToType = row.get('beToType')
                url = url_map[beToType].format(id)

                title = row.get('noticeTitle')
                pubTime = row.get('publishDate')

                mpProjectId = row.get('mpProjectId')
                mpProjectId = aes_cbc_decrypt_b64(mpProjectId) if isinstance(mpProjectId, str) else mpProjectId
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'mpProjectId': mpProjectId, 'id': id, 'beToType': beToType, 't': params['t']})

        if params['t'] == 6:
            url_map = {
                1: "https://xiangya.51eliao.com/#/web/purchaserWeb/consumableProjectResultNoticeDetail/{}/2",
            }
            for row in rows:
                id_raw = row.get('id')
                id = aes_cbc_decrypt_b64(id_raw) if isinstance(id_raw, str) else id_raw
                beToType = row.get('beToType')
                if beToType == 6:
                    continue

                url = url_map[beToType].format(id)

                title = row.get('noticeTitle')
                pubTime = row.get('publishDate')

                mpProjectId = row.get('mpProjectId')
                mpProjectId = aes_cbc_decrypt_b64(mpProjectId) if isinstance(mpProjectId, str) else mpProjectId
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'mpProjectId': mpProjectId, 'id': id, 'beToType': beToType, 't': params['t']})

        return ret_list

    def get_content(self, params: dict):
        # resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)
        # if 400 <= resp.status_code <= 599:
        #     return None

        for _ in range(8):
            try:
                resp = request.render_page(url=params['url'], sleep_time=3000)
                if resp:
                    break
            except:
                time.sleep(1.5)
                continue
        else:
            return None

        soup = BeautifulSoup(resp, "html.parser")
        content = soup.select_one('div.announcement-detail-panel')
        if not content:
            return None

        if a := content.select_one('.panel-head'):
            a.decompose()

        if "查看供应商资格" in str(content):
            a = """
            1、投标人基本资格条件：
            （1）具有独立承担民事责任的能力；
            （2）具有良好的商业信誉和健全的财务会计制度；
            （3）具有履行合同所必需的设备和专业技术能力；
            （4）有依法缴纳税收和社会保障资金的良好记录；
            （5）参加本项目招标活动前三年内，在经营活动中没有重大违法记录；
            （6）法律、行政法规规定的其他条件。
            2、投标人特定资格条件：无。
            3、单位负责人为同一人或者存在直接控股、管理关系的不同投标人，不得参加本项目同一合同项下的招标活动。
            4、与采购人存在利害关系可能影响招标公正性的法人、其他组织或者个人，不得参加投标。
            5、在投标截止时间前未被列入失信被执行人、重大税收违法案件当事人名单，未被列入政府采购严重违法失信行为记录名单。
            6、本项目为专门面向中小企业采购的项目。
            7、本次招标不接受联合体投标。
            """
            content = str(content).replace("查看供应商资格", a)

        if "查看领取文件要求" in str(content):
            b = "在51招标网上传法定代表人授权委托书（附身份证）、营业执照，以上资料均为加盖投标人原始公章的彩色扫描件。未按上述要求线上申请的，招标文件获取将不予受理。"
            content = str(content).replace("查看领取文件要求", b)

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}


if __name__ == "__main__":
    CrawlerObject().start()
