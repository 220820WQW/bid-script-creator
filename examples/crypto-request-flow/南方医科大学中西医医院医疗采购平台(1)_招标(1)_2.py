# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


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


def get_bid_info(bidPdFieldId):
    if not bidPdFieldId:
        return ''

    url = f"https://anno.51eliao.com/projectLog/selectPdByFieldId.do?bidPdFieldId={bidPdFieldId}&getDataTime=1782370368781"
    resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES)
    if 400 <= resp.status_code <= 599:
        return ''

    return resp.json().get('data')


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 采购结果公示 院内采购
            {
                "url": "https://anno.51eliao.com/hospital/site/selectAllPortalAnnouncementHbplatList.do?pageNum=1&pageSize=15&startTime=&endTime=&noticeTitle=&siteDomainName=nfzxy&getDataTime=1782377827869",
                "page_number": 1,
                't': 1
            },
            # 采购结果公示 耗材试剂
            {
                "url": "https://anno.51eliao.com/hospital/site/selectAllPortalAnnouncementConsumablesList.do?pageNum=1&pageSize=15&startTime=&endTime=&noticeTitle=&siteDomainName=nfzxy&getDataTime=1782379724617",
                "page_number": 1,
                't': 2
            },

            # 采购需求
            {
                "url": "https://beht.51eliao.com/ms/pdSurveyProject/selectListPublicProject?pageNum=1&pageSize=15&siteDomainName=nfzxy&projectName=&getDataTime=1782380089752",
                "page_number": 1,
                't': 3
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

        rows = resp.json().get('data').get('list')

        if params['t'] == 1:
            url_map = {
                1: "https://nfzxy.51eliao.com/#/web/purchaserWeb/projectResultNoticeDetail/{}/2",
                4: "https://nfzxy.51eliao.com/#/web/purchaserWeb/biddingProjectResultNoticeDetail/{}/2",
                5: "https://nfzxy.51eliao.com/#/web/purchaserWeb/biddingProjectResultNoticeDetail/{}/2",
                2: "https://nfzxy.51eliao.com/#/web/purchaserWeb/projectResultNoticeDetail/{}/2"
            }
            for row in rows:
                id = row.get('id')
                beToType = row.get('beToType')
                url = url_map[beToType].format(id)

                title = row.get('noticeTitle')
                pubTime = row.get('publishDate')

                mpProjectId = row.get('mpProjectId')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'mpProjectId': mpProjectId, 'id': id, 'beToType': beToType, 't': params['t']})
        if params['t'] == 2:
            url_map = {
                1: "https://nfzxy.51eliao.com/#/web/purchaserWeb/consumableProjectResultNoticeDetail/{}/2",
            }
            for row in rows:
                id = row.get('id')
                beToType = row.get('beToType')
                url = url_map[beToType].format(id)

                title = row.get('noticeTitle')
                pubTime = row.get('publishDate')

                mpProjectId = row.get('mpProjectId')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'mpProjectId': mpProjectId, 'id': id, 'beToType': beToType, 't': params['t']})
        if params['t'] == 3:
            for row in rows:
                pdSurveyProjectId = row.get('pdSurveyProjectId')
                url = f"https://nfzxy.51eliao.com/#/web/purchaserWeb/researchNoticeDetail/{pdSurveyProjectId}"

                title = row.get('projectName')
                pubTime = row.get('startTime')

                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'pdSurveyProjectId': pdSurveyProjectId, 'beToType': 0})

        return ret_list

    def get_content(self, params: dict):
        if params['beToType'] == 5 or params['beToType'] == 4:
            u1 = f"https://anno.51eliao.com/project/bidAnnouncementHistory/selectBidAnnouncementHistoryVO2?bidAnnouncementHistoryId={params['id']}&getDataTime=1782379214185"
            resp = auto_request(url=u1, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                return None

            d1 = resp.json().get('data')
            content = self.render_content(d1, params['beToType'], params['t'])

            u2 = f"https://anno.51eliao.com/hospital/site/getBidProjectSiteList.do?bidProjectId={params['mpProjectId']}&getDataTime=1782379214404"
            resp = auto_request(url=u2, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                content += ''
            else:
                d2 = resp.json().get('data')
                content += self.render_notice(d2)

        elif params['beToType'] == 1 or params['beToType'] == 2:
            u1 = f"https://anno.51eliao.com/project/wbBidAnnouncementHistory/selectWbBidAnnouncementHistoryVO2?wbBidAnnouncementHistoryId={params['id']}&getDataTime=1782378217678"
            resp = auto_request(url=u1, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                return None

            d1 = resp.json().get('data')
            content = self.render_content(d1, params['beToType'], params['t'])

            u2 = f"https://anno.51eliao.com/hospital/site/getMpProjectSiteList.do?mpProjectId={params['mpProjectId']}&getDataTime=1782378217980"
            resp = auto_request(url=u2, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                content += ''
            else:
                d2 = resp.json().get('data')
                content += self.render_notice(d2)

        elif params['beToType'] == 0:
            url = f"https://beht.51eliao.com/ms/pdSurveyProject/selectListPdSurveyProjectLogVO?pdSurveyProjectId={params['pdSurveyProjectId']}&getDataTime=1782380225156"
            resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                return None

            content = resp.json().get('data')[0].get('requirement')

        else:
            return None

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}

    def render_content(self, data, beToType, t):
        if t == 1:
            if beToType == 1:
                rows = ""
                for item in data.get('wbBidPackageHistoryVOList', []):
                    rows += f"""
                						<tr>
                							<td rowspan="1" colspan="1">
                								<div>{item.get('packageNumber', '')}</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>{item.get('packageName', '')}</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>{item.get('companyName', '')}</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>{item.get('rank', '')}</div>
                							</td>
                						</tr>
                        """
                content = f"""
                    <table>
                	<tbody>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>项目名称</div>
                			</td>
                			<td rowspan="1" colspan="3">
                				<div>{data.get('projectName', '')}</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>项目编号</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>{data.get('projectNumber', '')}</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>项目地点</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>{data.get('projectAddress', '')}</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>项目类型</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>{data.get('projectTypeName', '')}</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>开标时间</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>{data.get('obTime', '')}（北京时间）</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>采购人</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>{data.get('purchaser', '')}</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>联系人</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>{data.get('purchaserContacts', '')}</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>联系电话</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>{data.get('purchaserContactsPhone', '')}</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>联系地址</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>{data.get('purchaserContactsAddress', '')}</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>其他</div>
                			</td>
                			<td rowspan="1" colspan="3">
                				<div>{data.get('other', '')}</div>
                			</td>
                		</tr>
                	</tbody>
                </table>
                <div>
                	<p>中标(成交)供应商</p>
                	<div>
                		<div>
                			<div>
                				<table>
                					<thead>
                						<tr>
                							<th rowspan="1" colspan="1">
                								<div>包号</div>
                							</th>
                							<th rowspan="1" colspan="1">
                								<div>包名</div>
                							</th>
                							<th rowspan="1" colspan="1">
                								<div>供应商名称</div>
                							</th>
                							<th rowspan="1" colspan="1">
                								<div>排序</div>
                							</th>
                						</tr>
                					</thead>
                					<tbody>
                {rows}					</tbody>
                				</table>
                			</div>
                		</div>
                	</div>
                </div>
                    """
                return content

            elif beToType == 4:
                supplier_rows = ""
                for supplier in data.get('bidSuppliersPackageWbhistoryVOList', []):
                    supplier_rows += f"""
                            						<tr>
                            							<td rowspan="1" colspan="1">
                            								<div>{supplier.get('packageNumber', '')}</div>
                            							</td>
                            							<td rowspan="1" colspan="1">
                            								<div>{supplier.get('packageName', '')}</div>
                            							</td>
                            							<td rowspan="1" colspan="1">
                            								<div>{supplier.get('companyName', '')}</div>
                            							</td>
                            						</tr>
                                    """
                content = f"""
                                <table>
                            	<tbody>
                            		<tr>
                            			<td rowspan="1" colspan="1">
                            				<div>项目名称</div>
                            			</td>
                            			<td rowspan="1" colspan="3">
                            				<div>{data.get('projectName', '')}</div>
                            			</td>
                            		</tr>
                            		<tr>
                            			<td rowspan="1" colspan="1">
                            				<div>项目编号</div>
                            			</td>
                            			<td rowspan="1" colspan="1">
                            				<div>{data.get('projectNumber', '')}</div>
                            			</td>
                            			<td rowspan="1" colspan="1">
                            				<div>项目地点</div>
                            			</td>
                            			<td rowspan="1" colspan="1">
                            				<div>
                            					<p>{data.get('projectAddress', '')}</p>
                            				</div>
                            			</td>
                            		</tr>
                            		<tr>
                            			<td rowspan="1" colspan="1">
                            				<div>项目类型</div>
                            			</td>
                            			<td rowspan="1" colspan="1">
                            				<div>{data.get('projectTypeName', '')}</div>
                            			</td>
                            			<td rowspan="1" colspan="1">
                            				<div>竞价时间</div>
                            			</td>
                            			<td rowspan="1" colspan="1">
                            				<div>
                            					<div>
                            						<p>开始时间：{data.get('startTime', '')}（北京时间）</p>
                            						<p>截止时间：{data.get('endTime', '')}（北京时间）</p>
                            					</div>
                            				</div>
                            			</td>
                            		</tr>
                            		<tr>
                            			<td rowspan="1" colspan="1">
                            				<div>采购人</div>
                            			</td>
                            			<td rowspan="1" colspan="1">
                            				<div>{data.get('purchaser', '')}</div>
                            			</td>
                            			<td rowspan="1" colspan="1">
                            				<div>联系人</div>
                            			</td>
                            			<td rowspan="1" colspan="1">
                            				<div>
                            					<p>{data.get('purchaserContacts', '')}</p>
                            				</div>
                            			</td>
                            		</tr>
                            		<tr>
                            			<td rowspan="1" colspan="1">
                            				<div>联系电话</div>
                            			</td>
                            			<td rowspan="1" colspan="1">
                            				<div>{data.get('purchaserContactsPhone', '')}</div>
                            			</td>
                            			<td rowspan="1" colspan="1">
                            				<div>联系地址</div>
                            			</td>
                            			<td rowspan="1" colspan="1">
                            				<div>
                            					<p>{data.get('purchaserContactsAddress', '')}</p>
                            				</div>
                            			</td>
                            		</tr>
                            		<tr>
                            			<td rowspan="1" colspan="1">
                            				<div>其他</div>
                            			</td>
                            			<td rowspan="1" colspan="3">
                            				<div>{data.get('other', '')}</div>
                            			</td>
                            		</tr>
                            	</tbody>
                            </table>
                            <div>
                            	<p>成交供应商</p>
                            	<div>
                            		<div>
                            			<div>
                            				<div>
                            					<table>
                            						<thead>
                            							<tr>
                            								<th colspan="1" rowspan="1">
                            									<div>包号</div>
                            								</th>
                            								<th colspan="1" rowspan="1">
                            									<div>包名</div>
                            								</th>
                            								<th colspan="1" rowspan="1">
                            									<div>供应商名称</div>
                            								</th>
                            							</tr>
                            						</thead>
                            						<tbody>
                            {supplier_rows}						</tbody>
                            					</table>
                            				</div>
                            			</div>
                            		</div>
                            	</div>
                            </div>
                                """
                return content

            elif beToType == 5:
                supplier_rows = ""
                for supplier in data.get('bidSuppliersPackageWbhistoryVOList', []):
                    supplier_rows += f"""
                                            						<tr>
                                            							<td rowspan="1" colspan="1">
                                            								<div>{supplier.get('packageNumber', '')}</div>
                                            							</td>
                                            							<td rowspan="1" colspan="1">
                                            								<div>{supplier.get('packageName', '')}</div>
                                            							</td>
                                            							<td rowspan="1" colspan="1">
                                            								<div>{supplier.get('companyName', '')}</div>
                                            							</td>
                                            						</tr>
                                                    """
                content = f"""
                                                <table>
                                            	<tbody>
                                            		<tr>
                                            			<td rowspan="1" colspan="1">
                                            				<div>项目名称</div>
                                            			</td>
                                            			<td rowspan="1" colspan="3">
                                            				<div>{data.get('projectName', '')}</div>
                                            			</td>
                                            		</tr>
                                            		<tr>
                                            			<td rowspan="1" colspan="1">
                                            				<div>项目编号</div>
                                            			</td>
                                            			<td rowspan="1" colspan="1">
                                            				<div>{data.get('projectNumber', '')}</div>
                                            			</td>
                                            			<td rowspan="1" colspan="1">
                                            				<div>项目地点</div>
                                            			</td>
                                            			<td rowspan="1" colspan="1">
                                            				<div>
                                            					<p>{data.get('projectAddress', '')}</p>
                                            				</div>
                                            			</td>
                                            		</tr>
                                            		<tr>
                                            			<td rowspan="1" colspan="1">
                                            				<div>项目类型</div>
                                            			</td>
                                            			<td rowspan="1" colspan="1">
                                            				<div>{data.get('projectTypeName', '')}</div>
                                            			</td>
                                            			<td rowspan="1" colspan="1">
                                            				<div>竞价时间</div>
                                            			</td>
                                            			<td rowspan="1" colspan="1">
                                            				<div>
                                            					<div>
                                            						<p>开始时间：{data.get('startTime', '')}（北京时间）</p>
                                            						<p>截止时间：{data.get('endTime', '')}（北京时间）</p>
                                            					</div>
                                            				</div>
                                            			</td>
                                            		</tr>
                                            		<tr>
                                            			<td rowspan="1" colspan="1">
                                            				<div>采购人</div>
                                            			</td>
                                            			<td rowspan="1" colspan="1">
                                            				<div>{data.get('purchaser', '')}</div>
                                            			</td>
                                            			<td rowspan="1" colspan="1">
                                            				<div>联系人</div>
                                            			</td>
                                            			<td rowspan="1" colspan="1">
                                            				<div>
                                            					<p>{data.get('purchaserContacts', '')}</p>
                                            				</div>
                                            			</td>
                                            		</tr>
                                            		<tr>
                                            			<td rowspan="1" colspan="1">
                                            				<div>联系电话</div>
                                            			</td>
                                            			<td rowspan="1" colspan="1">
                                            				<div>{data.get('purchaserContactsPhone', '')}</div>
                                            			</td>
                                            			<td rowspan="1" colspan="1">
                                            				<div>联系地址</div>
                                            			</td>
                                            			<td rowspan="1" colspan="1">
                                            				<div>
                                            					<p>{data.get('purchaserContactsAddress', '')}</p>
                                            				</div>
                                            			</td>
                                            		</tr>
                                            		<tr>
                                            			<td rowspan="1" colspan="1">
                                            				<div>其他</div>
                                            			</td>
                                            			<td rowspan="1" colspan="3">
                                            				<div>{data.get('other', '')}</div>
                                            			</td>
                                            		</tr>
                                            	</tbody>
                                            </table>
                                            <div>
                                            	<p>成交供应商</p>
                                            	<div>
                                            		<div>
                                            			<div>
                                            				<div>
                                            					<table>
                                            						<thead>
                                            							<tr>
                                            								<th colspan="1" rowspan="1">
                                            									<div>包号</div>
                                            								</th>
                                            								<th colspan="1" rowspan="1">
                                            									<div>包名</div>
                                            								</th>
                                            								<th colspan="1" rowspan="1">
                                            									<div>供应商名称</div>
                                            								</th>
                                            							</tr>
                                            						</thead>
                                            						<tbody>
                                            {supplier_rows}						</tbody>
                                            					</table>
                                            				</div>
                                            			</div>
                                            		</div>
                                            	</div>
                                            </div>
                                                """
                return content

            elif beToType == 2:
                rows = ""
                for item in data.get('wbBidPackageHistoryVOList', []):
                    rows += f"""
                                						<tr>
                                							<td rowspan="1" colspan="1">
                                								<div>{item.get('packageNumber', '')}</div>
                                							</td>
                                							<td rowspan="1" colspan="1">
                                								<div>{item.get('packageName', '')}</div>
                                							</td>
                                							<td rowspan="1" colspan="1">
                                								<div>{item.get('companyName', '')}</div>
                                							</td>
                                							<td rowspan="1" colspan="1">
                                								<div>{item.get('rank', '')}</div>
                                							</td>
                                						</tr>
                                        """
                content = f"""
                                    <table>
                                	<tbody>
                                		<tr>
                                			<td rowspan="1" colspan="1">
                                				<div>项目名称</div>
                                			</td>
                                			<td rowspan="1" colspan="3">
                                				<div>{data.get('projectName', '')}</div>
                                			</td>
                                		</tr>
                                		<tr>
                                			<td rowspan="1" colspan="1">
                                				<div>项目编号</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('projectNumber', '')}</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>项目地点</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('projectAddress', '')}</div>
                                			</td>
                                		</tr>
                                		<tr>
                                			<td rowspan="1" colspan="1">
                                				<div>项目类型</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('projectTypeName', '')}</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>开标时间</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('obTime', '')}（北京时间）</div>
                                			</td>
                                		</tr>
                                		<tr>
                                			<td rowspan="1" colspan="1">
                                				<div>采购人</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('purchaser', '')}</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>联系人</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('purchaserContacts', '')}</div>
                                			</td>
                                		</tr>
                                		<tr>
                                			<td rowspan="1" colspan="1">
                                				<div>联系电话</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('purchaserContactsPhone', '')}</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>联系地址</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('purchaserContactsAddress', '')}</div>
                                			</td>
                                		</tr>
                                		<tr>
                                			<td rowspan="1" colspan="1">
                                				<div>其他</div>
                                			</td>
                                			<td rowspan="1" colspan="3">
                                				<div>{data.get('other', '')}</div>
                                			</td>
                                		</tr>
                                	</tbody>
                                </table>
                                <div>
                                	<p>中标(成交)供应商</p>
                                	<div>
                                		<div>
                                			<div>
                                				<table>
                                					<thead>
                                						<tr>
                                							<th rowspan="1" colspan="1">
                                								<div>包号</div>
                                							</th>
                                							<th rowspan="1" colspan="1">
                                								<div>包名</div>
                                							</th>
                                							<th rowspan="1" colspan="1">
                                								<div>供应商名称</div>
                                							</th>
                                							<th rowspan="1" colspan="1">
                                								<div>排序</div>
                                							</th>
                                						</tr>
                                					</thead>
                                					<tbody>
                                {rows}					</tbody>
                                				</table>
                                			</div>
                                		</div>
                                	</div>
                                </div>
                                    """
                return content

            else:
                return ''

        elif t == 2:
            if beToType == 1:
                rows = ""
                for item in data.get('consumablesTdPackageList', []):
                    rows += f"""
                                						<tr>
                                							<td rowspan="1" colspan="1">
                                								<div>{item.get('packageNumber', '')}</div>
                                							</td>
                                							<td rowspan="1" colspan="1">
                                								<div>{item.get('packageName', '')}</div>
                                							</td>
                                							<td rowspan="1" colspan="1">
                                								<div>{item.get('companyName', '')}</div>
                                							</td>
                                						</tr>
                                        """
                content = f"""
                                    <table>
                                	<tbody>
                                		<tr>
                                			<td rowspan="1" colspan="1">
                                				<div>项目名称</div>
                                			</td>
                                			<td rowspan="1" colspan="3">
                                				<div>{data.get('projectName', '')}</div>
                                			</td>
                                		</tr>
                                		<tr>
                                			<td rowspan="1" colspan="1">
                                				<div>项目编号</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('projectNumber', '')}</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>项目地点</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('projectAddress', '')}</div>
                                			</td>
                                		</tr>
                                		<tr>
                                			<td rowspan="1" colspan="1">
                                				<div>项目类型</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('projectTypeName', '')}</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>开标时间</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('obTime', '')}（北京时间）</div>
                                			</td>
                                		</tr>
                                		<tr>
                                			<td rowspan="1" colspan="1">
                                				<div>采购人</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('purchaser', '')}</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>联系人</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('purchaserContacts', '')}</div>
                                			</td>
                                		</tr>
                                		<tr>
                                			<td rowspan="1" colspan="1">
                                				<div>联系电话</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('purchaserContactsPhone', '')}</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>联系地址</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>{data.get('purchaserContactsAddress', '')}</div>
                                			</td>
                                		</tr>
                                		<tr>
                                			<td rowspan="1" colspan="1">
                                				<div>其他</div>
                                			</td>
                                			<td rowspan="1" colspan="3">
                                				<div>{data.get('other', '')}</div>
                                			</td>
                                		</tr>
                                	</tbody>
                                </table>
                                <div>
                                	<p>中标(成交)供应商</p>
                                	<div>
                                		<div>
                                			<div>
                                				<table>
                                					<thead>
                                						<tr>
                                							<th rowspan="1" colspan="1">
                                								<div>包号</div>
                                							</th>
                                							<th rowspan="1" colspan="1">
                                								<div>包名</div>
                                							</th>
                                							<th rowspan="1" colspan="1">
                                								<div>供应商名称</div>
                                							</th>
                                						</tr>
                                					</thead>
                                					<tbody>
                                {rows}					</tbody>
                                				</table>
                                			</div>
                                		</div>
                                	</div>
                                </div>
                                    """
                return content

            else:
                return ''

        else:
            return ''

    def render_notice(self, data):
        bid_type = {
            4: "成交补充",
            3: "结果公告",
            2: "流标公告",
            1: "采购公告",
        }
        rows = ""
        for item in data:
            beToType = item.get('beToType', '')
            rows += f"""
                <tr>
                    <td rowspan="1" colspan="1">
                        <div>
                            <p>{item.get('noticeTitle', '')}</p>
                        </div>
                    </td>
                    <td rowspan="1" colspan="1">
                        <div>
                            <p>{bid_type.get(beToType)}</p>
                        </div>
                    </td>
                    <td rowspan="1" colspan="1">
                        <div>
                            <p>{item.get('publishDate', '')}</p>
                        </div>
                    </td>
                </tr>"""

        content = f"""
            <div>
                <div>
                    <table>
                        <thead>
                            <tr>
                                <th colspan="1" rowspan="1">
                                    <div>公告名称</div>
                                </th>
                                <th colspan="1" rowspan="1">
                                    <div>公告类型</div>
                                </th>
                                <th colspan="1" rowspan="1">
                                    <div>发布时间</div>
                                </th>
                                <th></th>
                            </tr>
                        </thead>
                    </table>
                </div>
                <div>
                    <table>
                        <tbody>{rows}
                        </tbody>
                    </table>
                </div>
            </div>
            """
        return content


if __name__ == "__main__":
    CrawlerObject().start()
