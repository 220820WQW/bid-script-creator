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


HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Origin": "https://gdskin.51eliao.com",
    "Pragma": "no-cache",
    "Referer": "https://gdskin.51eliao.com/",
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


def get_bid_info(bidPdFieldId):
    url = f"https://anno.51eliao.com/projectLog/selectPdByFieldId.do?bidPdFieldId={bidPdFieldId}&getDataTime=1782453953667"
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
            # # 采购公告 院内采购
            {
                "url": "https://anno.51eliao.com/hospital/site/selectAllPortalMpProjectOneHbplatList.do?pageNum={}&pageSize=15&startTime=&endTime=&noticeTitle=&siteDomainName=gdskin&getDataTime=1782448928854",
                "page_number": 2,
                't': 1
            },
            # 采购公告 耗材试剂
            {
                "url": "https://anno.51eliao.com/hospital/site/selectAllPortalMpProjectOneConsumablesList.do?pageNum={}&pageSize=15&startTime=&endTime=&noticeTitle=&siteDomainName=gdskin&getDataTime=1782454534087",
                "page_number": 1,
                't': 2
            },

            # 采购公告变更 院内采购
            {
                "url": "https://anno.51eliao.com/hospital/site/selectAllPortalMpProjectChangeHbplatList.do?pageNum={}&pageSize=15&startTime=&endTime=&noticeTitle=&siteDomainName=gdskin&getDataTime=1782455581201",
                "page_number": 1,
                't': 3
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'].format(index), 't': p['t']
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
                5: "https://gdskin.51eliao.com/#/web/purchaserWeb/biddingProjectNoticeDetail/{}/2",
                1: "https://gdskin.51eliao.com/#/web/purchaserWeb/projectNoticeDetail/{}/2"
            }
            for row in rows:
                id = row.get('id')
                id = aes_cbc_decrypt_b64(id)
                beToType = row.get('beToType')
                url = url_map[beToType].format(id)

                title = row.get('noticeTitle')
                pubTime = row.get('publishDate')

                mpProjectId = row.get('mpProjectId')
                mpProjectId = aes_cbc_decrypt_b64(mpProjectId)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'mpProjectId': mpProjectId, 'id': id, 'beToType': beToType, 't': params['t']})
        if params['t'] == 2:
            for row in rows:
                id = row.get('id')
                id = aes_cbc_decrypt_b64(id)
                beToType = row.get('beToType')
                url = f"https://gdskin.51eliao.com/#/web/purchaserWeb/consumableProjectNoticeDetail/{id}/2"

                title = row.get('noticeTitle')
                pubTime = row.get('publishDate')

                mpProjectId = row.get('mpProjectId')
                mpProjectId = aes_cbc_decrypt_b64(mpProjectId)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'mpProjectId': mpProjectId, 'id': id, 'beToType': beToType, 't': params['t']})
        if params['t'] == 3:
            url_map = {
                2: "https://gdskin.51eliao.com/#/web/purchaserWeb/projectNoticeDetail/{}/1",
                11: "https://gdskin.51eliao.com/#/web/purchaserWeb/recallProjectNoticeDetail/{}",
                12: "https://gdskin.51eliao.com/#/web/purchaserWeb/recallBiddingProjectNoticeDetail/{}"
            }
            for row in rows:
                id = row.get('id')
                id = aes_cbc_decrypt_b64(id)
                beToType = row.get('beToType')
                url = url_map[beToType].format(id)

                title = row.get('noticeTitle')
                pubTime = row.get('publishDate')

                mpProjectId = row.get('mpProjectId')
                mpProjectId = aes_cbc_decrypt_b64(mpProjectId)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'mpProjectId': mpProjectId, 'id': id, 'beToType': beToType, 't': params['t']})

        return ret_list

    def get_content(self, params: dict):
        if params['beToType'] == 1 or params['beToType'] == 2:
            u1 = f"https://anno.51eliao.com/project/portalAcSearch/getPortalMpProjectById/{params['id']}?getDataTime=1782296614096"
            resp = auto_request(url=u1, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                return None

            d1 = resp.json().get('data')
            content = self.render_content(d1, params['beToType'], params['t'])

            u2 = f"https://anno.51eliao.com/hospital/site/getMpProjectSiteList.do?mpProjectId={params['mpProjectId']}&getDataTime=1782296614411"
            resp = auto_request(url=u2, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                content += ""
            else:
                d2 = resp.json().get('data')
                content += self.render_notice(d2)

        elif params['beToType'] == 5:
            u1 = f"https://anno.51eliao.com/site/getBidProjectLogVO.do?id={params['id']}&getDataTime=1782453345390"
            resp = auto_request(url=u1, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                return None

            d1 = resp.json().get('data')
            content = self.render_content(d1, params['beToType'], params['t'])

            u2 = f"https://anno.51eliao.com/hospital/site/getBidProjectSiteList.do?bidProjectId={params['mpProjectId']}&getDataTime=1782453345610"
            resp = auto_request(url=u2, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                content += ""
            else:
                d2 = resp.json().get('data')
                content += self.render_notice(d2)

        elif params['beToType'] == 11:
            u1 = f"https://anno.51eliao.com/site/getMpProjectNoticeVO.do?mpProjectId={params['id']}&getDataTime=1782456625494"
            resp = auto_request(url=u1, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                return None

            d1 = resp.json().get('data')
            content = self.render_content(d1, params['beToType'], params['t'])

            u2 = f"https://anno.51eliao.com/hospital/site/getMpProjectSiteList.do?mpProjectId={params['mpProjectId']}&getDataTime=1782456625494"
            resp = auto_request(url=u2, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                content += ""
            else:
                d2 = resp.json().get('data')
                content += self.render_notice(d2)

        elif params['beToType'] == 12:
            u1 = f"https://anno.51eliao.com/site/getBidProjectLogCancelVO.do?bidProjectId={params['id']}&getDataTime=1782457008185"
            resp = auto_request(url=u1, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                return None

            d1 = resp.json().get('data')
            content = self.render_content(d1, params['beToType'], params['t'])

            u2 = f"https://anno.51eliao.com/hospital/site/getBidProjectSiteList.do?bidProjectId={params['mpProjectId']}&getDataTime=1782457008185"
            resp = auto_request(url=u2, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                content += ""
            else:
                d2 = resp.json().get('data')
                content += self.render_notice(d2)

        else:
            return None

        content = handle_str.completion_url(str(content), params['url'])
        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}

    def render_content(self, data, beToType, t):
        if t == 1:
            if beToType == 1:
                rows = ""
                for item in data.get('mpProjectTargetHistoryVOList', []):
                    rows += f"""
                						<tr>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('packageNumber', '')}</p>
                								</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('packageName', '')}</p>
                								</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('itemName', '')}</p>
                								</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('number', '')}</p>
                								</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('unit', '')}</p>
                								</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('procurementBudget', '')}</p>
                								</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('buyingLeads', '')}</p>
                								</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('remarks', '')}</p>
                								</div>
                							</td>
                						</tr>
                """
                content = f"""
                    <table>
                	<tbody>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>项目名称</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="3">
                				<div>
                					<p>{data.get('projectName', '')}</p>
                				</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>委托编号</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>{data.get('projectNumber', '')}</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>项目地点</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>{data.get('projectAddress', '')}</p>
                				</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>项目类型</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>{data.get('projectTypeName', '')}</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>竞标方式</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>{data.get('bidModel', '')}</p>
                				</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>供应商资格</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>
                					供应商资格要求
                                    1、供应商基本资格条件：
                                    1.1具有独立承担民事责任的能力；
                                    1.2具有履行合同所必需的设备和专业技术能力；
                                    1.3参加本项目采购活动前三年内，在经营活动中没有重大违法记录；
                                    1.4在响应截止时间前未被列入失信被执行人、重大税收违法案件当事人名单，未被列入政府采购严重违法失信行为记录名单；
                                    1.5法律、行政法规规定的其他条件。
                                    2、供应商特定资格条件：
                                    （1）所投产品如纳入医疗器械管理的，供应商必须具备食品药品监督管理部门颁发的有效的《医疗器械经营备案凭证》复印件（适用于第二类医疗器械）或有效的《医疗器械经营许可证》复印件（适用于第三类医疗器械）；如为生产企业参与响应的，须提供监督管理部门签发的有效的《医疗器械生产备案凭证》或《医疗器械生产许可证》；
                                    （2）所投产品如纳入医疗器械管理的，该产品必须具备食品药品监督管理部门颁发的医疗器械备案凭证（一类）或医疗器械注册证（二、三类）复印件。所投产品如未纳入医疗器械管理的，提供分类界定证明或说明。
                                    3、单位负责人为同一人或者存在直接控股、管理关系的不同供应商，不得参加本项目同一合同项下的采购活动。
                                    4、本次采购不接受联合体响应。
                                    5、依据本院供应商不良行为及黑名单管理要求，被本院列入黑名单、处于惩戒有效期的供应商，禁止参与本院所有采购项目投标、磋商、询价、竞价等一切采购活动，本次项目不接受其参与报名及投标。
                					</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>公告方式</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>{data.get('tenderMethodName', '')}</p>
                				</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>文件是否收费</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>{data.get('filePrice', '')}</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>领取文件要求</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>{data.get('pbAsk', '')}</p>
                				</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>文件售价</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>{data.get('filePrice', '')}</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>购标起止时间</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<div>
                						<p>开始时间：{data.get('suTime', '')}</p>
                						<p>截止时间：{data.get('byTime', '')}</p>
                					</div>
                				</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>开标时间</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>{data.get('obTime', '')}</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>开标地点</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>https://51eliao.com</p>
                				</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>采购人</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>{data.get('purchaser', '')}</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>联系人</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>{data.get('pContacts', '')}</p>
                				</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>联系电话</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>{data.get('pContactsPhone', '')}</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>联系地址</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>{data.get('pAddress', '')}</p>
                				</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>其他</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="3">
                				<div>
                					<p>{data.get('other', '')}</p>
                				</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>备注</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="3">
                				<div>
                					<p>{data.get('pbAsk', '')}</p>
                				</div>
                			</td>
                		</tr>
                	</tbody>
                </table>
                <div>
                	<p>标的信息</p>
                	<div>
                		<div>
                			<div>
                				<div>
                					<div>
                						<div>
                							<div>
                								<div>
                									<table>
                										<thead>
                											<tr>
                												<th rowspan="1" colspan="1">
                													<div>
                														<span>包号</span>
                													</div>
                												</th>
                												<th rowspan="1" colspan="1">
                													<div>
                														<span>包名</span>
                													</div>
                												</th>
                												<th rowspan="1" colspan="1">
                													<div>
                														<span>品目名称</span>
                													</div>
                												</th>
                												<th rowspan="1" colspan="1">
                													<div>
                														<span>数量</span>
                													</div>
                												</th>
                												<th rowspan="1" colspan="1">
                													<div>
                														<span>单位</span>
                													</div>
                												</th>
                												<th rowspan="1" colspan="1">
                													<div>
                														<span>采购预算(元)</span>
                													</div>
                												</th>
                												<th rowspan="1" colspan="1">
                													<div>
                														<span>采购需求</span>
                													</div>
                												</th>
                												<th rowspan="1" colspan="1">
                													<div>
                														<span>备注</span>
                													</div>
                												</th>
                											</tr>
                										</thead>
                										<tbody>{rows}
                										</tbody>
                									</table>
                								</div>
                							</div>
                						</div>
                					</div>
                				</div>
                			</div>
                		</div>
                	</div>
                </div>
                    """
                return content

            elif beToType == 5:
                rows = ""
                for item in data.get('targetLogVOS', []):
                    bid_info = get_bid_info(item.get('bidPdFieldId', ''))
                    rows += f"""
                        <tr>
                            <td rowspan="1" colspan="1">{item.get('packageNumber', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('packageName', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('itemName', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('number', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('unit', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('procurementBudget', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('procurementBudget', '')}</td>
                            <td rowspan="1" colspan="1">{bid_info}</td>
                            <td rowspan="1" colspan="1">{item.get('remarks', '')}</td>
                        </tr>
                        """
                content = f"""
                <table>
                    <tbody>
                        <tr>
                            <td rowspan="1" colspan="1">项目名称</td>
                            <td rowspan="1" colspan="3">{data.get('projectName', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">项目编号</td>
                            <td rowspan="1" colspan="1">{data.get('projectNumber', '')}</td>
                            <td rowspan="1" colspan="1">项目地点</td>
                            <td rowspan="1" colspan="1">{data.get('projectLocation', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">项目类型</td>
                            <td rowspan="1" colspan="1">{data.get('projectTypeName', '')}</td>
                            <td rowspan="1" colspan="1">供应商资格</td>
                            <td rowspan="1" colspan="1">
                            1、供应商基本资格条件：
                            （1）具有独立承担民事责任的能力；
                            （2）具有履行合同所必需的设备和专业技术能力；
                            （3）具有良好的商业信誉和健全的财务会计制度；
                            （4）近三年内，在经营活动中没有违法记录；
                            （5）法律、行政法规规定的其他条件；
                            2、供应商特定资格条件：无。
                            3、单位负责人为同一人或者存在直接控股、管理关系的不同供应商，不得参加本项目同一合同项下的竞价活动。
                            4、在竞价截止时间前未被列入失信被执行人、重大税收违法案件当事人名单，未被列入政府采购严重违法失信行为记录名单。
                            5、本次竞价不接受联合体参与。
                            </td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">报名时间</td>
                            <td rowspan="1" colspan="3">
                                <p>开始时间：{data.get('suTime', '')}</p>
                                <p>截止时间：{data.get('byTime', '')}</p>
                            </td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">报名资料要求</td>
                            <td rowspan="1" colspan="3">{data.get('registrationRemarks', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">公告方式</td>
                            <td rowspan="1" colspan="1">{data.get('bidModelName', '')}</td>
                            <td rowspan="1" colspan="1">报价方式</td>
                            <td rowspan="1" colspan="1">{data.get('quotationMethodName', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">竞价轮次</td>
                            <td rowspan="1" colspan="1">{data.get('bidRounds', '')}</td>
                            <td rowspan="1" colspan="1">出价间隔时间</td>
                            <td rowspan="1" colspan="1">{data.get('bidInterval', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">最小降价幅度</td>
                            <td rowspan="1" colspan="1">{data.get('range', '')}</td>
                            <td rowspan="1" colspan="1">竞价时间</td>
                            <td rowspan="1" colspan="1">
                                <p>开始时间：{data.get('startTime', '')}</p>
                                <p>截止时间：{data.get('endTime', '')}</p>
                            </td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">采购人</td>
                            <td rowspan="1" colspan="1">{data.get('purchaser', '')}</td>
                            <td rowspan="1" colspan="1">联系人</td>
                            <td rowspan="1" colspan="1">{data.get('purchaserConcat', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">联系电话</td>
                            <td rowspan="1" colspan="1">{data.get('purchaserConcatPhone', '')}</td>
                            <td rowspan="1" colspan="1">联系地址</td>
                            <td rowspan="1" colspan="1">{data.get('purchaserAddress', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">报价资料要求</td>
                            <td rowspan="1" colspan="3">{data.get('quotedInfoRemarks', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">竞价地点</td>
                            <td rowspan="1" colspan="3">https://51eliao.com</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">其他</td>
                            <td rowspan="1" colspan="3">{data.get('other', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">备注</td>
                            <td rowspan="1" colspan="3">1、供应商在“51医疗采购平台”免费注册、完善用户信息并获得审核通过后，可自行登录账号，点击页面右下方“帮助”按钮，通过观看“操作视频”或“操作手册”查询具体操作流程。2、供应商通过“51医疗采购平台”参与竞价项目前，必须登录“51医疗采购平台”申请数字CA证书并完成缴费（CA仅适用于竞标文件加、解密，购标环节无需使用）。已成功申领平台数字CA证书且在有效期内的（有效期：1年），CA证书可重复使用。（平台技术支持电话：0731-82889851）</td>
                        </tr>
                    </tbody>
                </table>
                <div>
                    <p>标的信息</p>
                    <table>
                        <thead>
                            <tr>
                                <th rowspan="1" colspan="1">包号</th>
                                <th rowspan="1" colspan="1">包名</th>
                                <th rowspan="1" colspan="1">品目名称</th>
                                <th rowspan="1" colspan="1">数量</th>
                                <th rowspan="1" colspan="1">单位</th>
                                <th rowspan="1" colspan="1">采购预算(元)</th>
                                <th rowspan="1" colspan="1">采购限价(元)</th>
                                <th rowspan="1" colspan="1">采购需求</th>
                                <th rowspan="1" colspan="1">备注</th>
                            </tr>
                        </thead>
                        <tbody>
                {rows}
                        </tbody>
                    </table>
                </div>
                    """
                return content

            else:
                return ''

        if t == 2:
            if beToType == 1:
                rows = ""
                for item in data.get('itemHistoryVOList', []):
                    rows += f"""
                        <tr>
                            <td rowspan="1" colspan="1">{item.get('packageNumber', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('packageName', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('catalogNumber', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('directoryName', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('finalistsNum', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('supplyPeriod', '')}</td>
                        </tr>
                        """
                content = f"""
                <table>
                    <tbody>
                        <tr>
                            <td rowspan="1" colspan="1">项目名称</td>
                            <td rowspan="1" colspan="3">{data.get('projectName', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">委托编号</td>
                            <td rowspan="1" colspan="1">{data.get('projectNumber', '')}</td>
                            <td rowspan="1" colspan="1">项目地点</td>
                            <td rowspan="1" colspan="1">{data.get('projectAddress', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">项目类型</td>
                            <td rowspan="1" colspan="1">{data.get('projectTypeName', '')}</td>
                            <td rowspan="1" colspan="1">竞标方式</td>
                            <td rowspan="1" colspan="1">{data.get('bidModel', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">供应商资格</td>
                            <td rowspan="1" colspan="1">
                            1、在中华人民共和国境内注册，具备独立法人资格，近三个月内依法缴纳税收和社会保障资金。
                            2、所投医用耗材/试剂生产或经营纳入行政管理的，供应商须具有相应的生产或经营许可证（如医疗器械生产或经营备案凭证、医疗器械生产或经营许可证、生产企业卫生许可证等）。
                            3、所投医用耗材/试剂纳入行政管理的，耗材须具有相应的备案凭证或注册证（如医疗器械备案凭证、医疗器械注册证、卫生许可批件、消毒产品安全性评价报告等）。
                            4、所报耗材属于广东省或广州市医用耗材交易平台挂网交易品种（提供平台图片证明）；
                            5、单位负责人为同一人或者存在控股、管理关系的不同单位，不得同时参加同一包号的申请，否则均取消本项目的入围资格。
                            6、与采购人存在利害关系可能影响入围公正性的法人、其他组织或者个人，不得申请。
                            7、在截止时间前被“信用中国”网站列入失信被执行人或重大税收违法案件当事人名单的、或被“中国政府采购网”网站列入政府采购严重违法失信行为记录名单（处罚期限尚未届满的）的单位，不得申请。
                            8、本项目不接受联合体申请。
                            9、符合法律、行政法规规定的其他条件。
                            </td>
                            <td rowspan="1" colspan="1">公告方式</td>
                            <td rowspan="1" colspan="1">{data.get('tenderMethodName', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">文件是否收费</td>
                            <td rowspan="1" colspan="1">{data.get('whetherPdName', '')}</td>
                            <td rowspan="1" colspan="1">领取文件要求</td>
                            <td rowspan="1" colspan="1">{data.get('pbAsk', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">文件售价</td>
                            <td rowspan="1" colspan="1">{data.get('filePrice', '')}</td>
                            <td rowspan="1" colspan="1">购标起止时间</td>
                            <td rowspan="1" colspan="1">
                                <p>开始时间：{data.get('suTime', '')}</p>
                                <p>截止时间：{data.get('byTime', '')}</p>
                            </td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">开标时间</td>
                            <td rowspan="1" colspan="1">{data.get('obTime', '')}</td>
                            <td rowspan="1" colspan="1">开标地点</td>
                            <td rowspan="1" colspan="1">{data.get('otherUrl', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">采购人</td>
                            <td rowspan="1" colspan="1">{data.get('purchaser', '')}</td>
                            <td rowspan="1" colspan="1">联系人</td>
                            <td rowspan="1" colspan="1">{data.get('pContacts', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">联系电话</td>
                            <td rowspan="1" colspan="1">{data.get('pContactsPhone', '')}</td>
                            <td rowspan="1" colspan="1">联系地址</td>
                            <td rowspan="1" colspan="1">{data.get('pAddress', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">其他</td>
                            <td rowspan="1" colspan="3">{data.get('other', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">备注</td>
                            <td rowspan="1" colspan="3">{data.get('operationRemarks', '')}</td>
                        </tr>
                    </tbody>
                </table>
                <div>
                    <p>标的信息</p>
                    <table>
                        <thead>
                            <tr>
                                <th rowspan="1" colspan="1">包号</th>
                                <th rowspan="1" colspan="1">包名</th>
                                <th rowspan="1" colspan="1">目录序号</th>
                                <th rowspan="1" colspan="1">目录名称</th>
                                <th rowspan="1" colspan="1">入围数量</th>
                                <th rowspan="1" colspan="1">供应期</th>
                            </tr>
                        </thead>
                        <tbody>
                {rows}
                        </tbody>
                    </table>
                </div>
                    """
                return content

            else:
                return ''

        if t == 3:
            if beToType == 2:
                rows = ""
                for item in data.get('itemHistoryVOList', []) or []:
                    rows += f"""
                        <tr>
                            <td rowspan="1" colspan="1">{item.get('packageNumber', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('packageName', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('catalogNumber', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('directoryName', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('finalistsNum', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('supplyPeriod', '')}</td>
                            <td rowspan="1" colspan="1">{item.get('remarks', '')}</td>
                        </tr>
                        """
                content = f"""
                <table>
                    <tbody>
                        <tr>
                            <td rowspan="1" colspan="1">项目名称</td>
                            <td rowspan="1" colspan="3">{data.get('projectName', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">委托编号</td>
                            <td rowspan="1" colspan="1">{data.get('projectNumber', '')}</td>
                            <td rowspan="1" colspan="1">项目地点</td>
                            <td rowspan="1" colspan="1">{data.get('projectAddress', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">项目类型</td>
                            <td rowspan="1" colspan="1">{data.get('projectTypeName', '')}</td>
                            <td rowspan="1" colspan="1">竞标方式</td>
                            <td rowspan="1" colspan="1">{data.get('bidModel', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">供应商资格</td>
                            <td rowspan="1" colspan="1">
                            1、供应商基本资格条件：
                            1.1具有独立承担民事责任的能力；
                            1.2具有履行合同所必需的设备和专业技术能力；
                            1.3参加本项目采购活动前三年内，在经营活动中没有重大违法记录；
                            1.4在响应截止时间前未被列入失信被执行人、重大税收违法案件当事人名单，未被列入政府采购严重违法失信行为记录名单；
                            1.5法律、行政法规规定的其他条件。
                            2、供应商特定资格条件：供应商须提供有效的食品经营或生产资质证明：
                            2.1、若供应商为经销商须提供《食品经营许可证》（经营项目须含预包装食品销售）或《仅销售预包装食品备案凭证》；
                            2.2、若供应商为生产厂家的须提供《食品生产许可证》（产品明细须包含粽子或相关品类）。
                            3、单位负责人为同一人或者存在直接控股、管理关系的不同供应商，不得参加本项目同一合同项下的采购活动，一经发现按废标处理并标记为不诚信供应商。
                            4、本次采购不接受联合体响应。
                            </td>
                            <td rowspan="1" colspan="1">公告方式</td>
                            <td rowspan="1" colspan="1">{data.get('tenderMethodName', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">文件是否收费</td>
                            <td rowspan="1" colspan="1">{data.get('whetherPdName', '')}</td>
                            <td rowspan="1" colspan="1">领取文件要求</td>
                            <td rowspan="1" colspan="1">{data.get('pbAsk', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">文件售价</td>
                            <td rowspan="1" colspan="1">{data.get('filePrice', '')}</td>
                            <td rowspan="1" colspan="1">购标起止时间</td>
                            <td rowspan="1" colspan="1">
                                <p>开始时间：{data.get('suTime', '')}</p>
                                <p>截止时间：{data.get('byTime', '')}</p>
                            </td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">开标时间</td>
                            <td rowspan="1" colspan="1">{data.get('obTime', '')}</td>
                            <td rowspan="1" colspan="1">开标地点</td>
                            <td rowspan="1" colspan="1">{data.get('otherUrl', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">采购人</td>
                            <td rowspan="1" colspan="1">{data.get('purchaser', '')}</td>
                            <td rowspan="1" colspan="1">联系人</td>
                            <td rowspan="1" colspan="1">{data.get('pContacts', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">联系电话</td>
                            <td rowspan="1" colspan="1">{data.get('pContactsPhone', '')}</td>
                            <td rowspan="1" colspan="1">联系地址</td>
                            <td rowspan="1" colspan="1">{data.get('pAddress', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">其他</td>
                            <td rowspan="1" colspan="3">{data.get('other', '')}</td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">备注</td>
                            <td rowspan="1" colspan="3">{data.get('operationRemarks', '')}</td>
                        </tr>
                    </tbody>
                </table>
                <div>
                    <p>标的信息</p>
                    <table>
                        <thead>
                            <tr>
                                <th rowspan="1" colspan="1">包号</th>
                                <th rowspan="1" colspan="1">包名</th>
                                <th rowspan="1" colspan="1">目录序号</th>
                                <th rowspan="1" colspan="1">目录名称</th>
                                <th rowspan="1" colspan="1">入围数量</th>
                                <th rowspan="1" colspan="1">供应期</th>
                                <th rowspan="1" colspan="1">备注</th>
                            </tr>
                        </thead>
                        <tbody>
                {rows}
                        </tbody>
                    </table>
                </div>
                    """
                return content

            elif beToType == 11:
                content = f"""
                    <table>
                	<tbody>
                		<tr>
                			<td rowspan="1" colspan="1">项目名称</td>
                			<td rowspan="1" colspan="3">{data.get('projectName', '')}</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">项目编号</td>
                			<td rowspan="1" colspan="1">{data.get('projectNumber', '')}</td>
                			<td rowspan="1" colspan="1">项目地点</td>
                			<td rowspan="1" colspan="1">{data.get('projectAddress', '')}</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">项目类型</td>
                			<td rowspan="1" colspan="1">{data.get('projectType', '')}</td>
                			<td rowspan="1" colspan="1">竞标方式</td>
                			<td rowspan="1" colspan="1">{data.get('bidModel', '')}</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">采购人</td>
                			<td rowspan="1" colspan="1">{data.get('purchaser', '')}</td>
                			<td rowspan="1" colspan="1">联系人</td>
                			<td rowspan="1" colspan="1">{data.get('pcontacts', '')}</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">联系电话</td>
                			<td rowspan="1" colspan="1">{data.get('pcontactsPhone', '')}</td>
                			<td rowspan="1" colspan="1">联系地址</td>
                			<td rowspan="1" colspan="1">{data.get('paddress', '')}</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">撤项/流标原因</td>
                			<td rowspan="1" colspan="3">{data.get('operationRemarks', '')}</td>
                		</tr>
                	</tbody>
                </table>
                    """
                return content

            elif beToType == 12:
                content = f"""
                    <table>
                	<tbody>
                		<tr>
                			<td rowspan="1" colspan="1">项目名称</td>
                			<td rowspan="1" colspan="3">{data.get('projectName', '')}</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">项目编号</td>
                			<td rowspan="1" colspan="1">{data.get('projectNumber', '')}</td>
                			<td rowspan="1" colspan="1">项目地点</td>
                			<td rowspan="1" colspan="1">{data.get('projectLocation', '')}</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">项目类型</td>
                			<td rowspan="1" colspan="1">{data.get('projectTypeName', '')}</td>
                			<td rowspan="1" colspan="1">公告方式</td>
                			<td rowspan="1" colspan="1">{data.get('bidModelName', '')}</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">采购人</td>
                			<td rowspan="1" colspan="1">{data.get('purchaser', '')}</td>
                			<td rowspan="1" colspan="1">联系人</td>
                			<td rowspan="1" colspan="1">{data.get('purchaserConcat', '')}</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">联系电话</td>
                			<td rowspan="1" colspan="1">{data.get('purchaserConcatPhone', '')}</td>
                			<td rowspan="1" colspan="1">联系地址</td>
                			<td rowspan="1" colspan="1">{data.get('purchaserAddress', '')}</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">撤项原因</td>
                			<td rowspan="1" colspan="3">{data.get('releaseRemarks', '')}</td>
                		</tr>
                	</tbody>
                </table>
                    """
                return content

            else:
                return ''

        else:
            return ''

    def render_notice(self, data):
        bid_type = {
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
