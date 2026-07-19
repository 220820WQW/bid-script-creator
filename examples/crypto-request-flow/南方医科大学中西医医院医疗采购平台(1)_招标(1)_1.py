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
            # 采购公告 院内采购
            {
                "url": "https://anno.51eliao.com/hospital/site/selectAllPortalMpProjectOneHbplatList.do?pageNum=1&pageSize=15&startTime=&endTime=&noticeTitle=&siteDomainName=nfzxy&getDataTime=1782374219411",
                "page_number": 1,
                't': 1
            },
            # 采购公告 耗材试剂
            {
                "url": "https://anno.51eliao.com/hospital/site/selectAllPortalMpProjectOneConsumablesList.do?pageNum=1&pageSize=15&startTime=&endTime=&noticeTitle=&siteDomainName=nfzxy&getDataTime=1782374325108",
                "page_number": 1,
                't': 2
            },

            # 采购公告变更 院内采购
            {
                "url": "https://anno.51eliao.com/hospital/site/selectAllPortalMpProjectChangeHbplatList.do?pageNum=1&pageSize=15&startTime=&endTime=&noticeTitle=&siteDomainName=nfzxy&getDataTime=1782375288549",
                "page_number": 1,
                't': 3
            },
            # 采购公告变更 耗材试剂
            {
                "url": "https://anno.51eliao.com/hospital/site/selectAllPortalMpProjectChangeConsumablesList.do?pageNum=1&pageSize=15&startTime=&endTime=&noticeTitle=&siteDomainName=nfzxy&getDataTime=1782377495331",
                "page_number": 1,
                't': 4
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
                5: "https://nfzxy.51eliao.com/#/web/purchaserWeb/biddingProjectNoticeDetail/{}/2",
                1: "https://nfzxy.51eliao.com/#/web/purchaserWeb/projectNoticeDetail/{}/2"
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

                title = row.get('noticeTitle')
                pubTime = row.get('publishDate')

                if beToType == 1:
                    url = f"https://nfzxy.51eliao.com/#/web/purchaserWeb/consumableProjectNoticeDetail/{id}/2"
                else:
                    url = f"https://nfzxy.51eliao.com/#/web/purchaserWeb/otherNoticeDetail/{id}/2"

                    u = f"https://anno.51eliao.com/site/getMpNoticeInfo.do?mpNoticeId={id}&getDataTime=1782374710777"
                    resp = auto_request(url=u, headers=HEADERS, cookies=COOKIES)
                    if 400 <= resp.status_code <= 599:
                        continue
                    else:
                        content = resp.json().get('data').get('content')
                        content = handle_str.completion_url(str(content), params['url'])
                        ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'content': content})
                        continue

                mpProjectId = row.get('mpProjectId')
                mpProjectId = aes_cbc_decrypt_b64(mpProjectId)
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'mpProjectId': mpProjectId, 'id': id, 'beToType': beToType, 't': params['t']})
        if params['t'] == 3:
            url_map = {
                11: "https://nfzxy.51eliao.com/#/web/purchaserWeb/recallProjectNoticeDetail/{}",
                2: "https://nfzxy.51eliao.com/#/web/purchaserWeb/projectNoticeDetail/{}/1",
                12: "https://nfzxy.51eliao.com/#/web/purchaserWeb/recallBiddingProjectNoticeDetail/{}"
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
        if params['t'] == 4:
            url_map = {
                11: "https://nfzxy.51eliao.com/#/web/purchaserWeb/recallProjectNoticeDetail/{}",
                2: "https://nfzxy.51eliao.com/#/web/purchaserWeb/consumableProjectNoticeDetail/{}/1",
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
        if params.get('content'):
            return params

        if params['beToType'] == 5:
            u1 = f"https://anno.51eliao.com/site/getBidProjectLogVO.do?id={params['id']}&getDataTime=1782368554274"
            resp = auto_request(url=u1, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                return None

            d1 = resp.json().get('data')
            content = self.render_content(d1, params['beToType'], params['t'])

            u2 = f"https://anno.51eliao.com/hospital/site/getBidProjectSiteList.do?bidProjectId={params['mpProjectId']}&getDataTime=1782370366085"
            resp = auto_request(url=u2, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                content += ''
            else:
                d2 = resp.json().get('data')
                content += self.render_notice(d2)

        elif params['beToType'] == 1 or params['beToType'] == 2:
            u1 = f"https://anno.51eliao.com/project/portalAcSearch/getPortalMpProjectById/{params['id']}?getDataTime=1782372198653"
            resp = auto_request(url=u1, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                return None

            d1 = resp.json().get('data')
            content = self.render_content(d1, params['beToType'], params['t'])

            u2 = f"https://anno.51eliao.com/hospital/site/getMpProjectSiteList.do?mpProjectId={params['mpProjectId']}&getDataTime=1782372198845"
            resp = auto_request(url=u2, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                content += ''
            else:
                d2 = resp.json().get('data')
                content += self.render_notice(d2)

        elif params['beToType'] == 11:
            u1 = f"https://anno.51eliao.com/site/getMpProjectNoticeVO.do?mpProjectId={params['id']}&getDataTime=1782375896574"
            resp = auto_request(url=u1, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                return None

            d1 = resp.json().get('data')
            content = self.render_content(d1, params['beToType'], params['t'])

            u2 = f"https://anno.51eliao.com/hospital/site/getMpProjectSiteList.do?mpProjectId={params['mpProjectId']}&getDataTime=1782376943877"
            resp = auto_request(url=u2, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                content += ''
            else:
                d2 = resp.json().get('data')
                content += self.render_notice(d2)

        elif params['beToType'] == 12:
            u1 = f"https://anno.51eliao.com/site/getBidProjectLogCancelVO.do?bidProjectId={params['id']}&getDataTime=1782377094318"
            resp = auto_request(url=u1, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                return None

            d1 = resp.json().get('data')
            content = self.render_content(d1, params['beToType'], params['t'])

            u2 = f"https://anno.51eliao.com/hospital/site/getBidProjectSiteList.do?bidProjectId={params['mpProjectId']}&getDataTime=1782377094318"
            resp = auto_request(url=u2, headers=HEADERS, cookies=COOKIES)
            if 400 <= resp.status_code <= 599:
                content += ''
            else:
                d2 = resp.json().get('data')
                content += self.render_notice(d2)

        else:
            return None

        content = handle_str.completion_url(str(content), params['url'])
        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}

    def render_content(self, data, beToType, t):
        if t == 1:
            if beToType == 5:
                target_rows = ""
                for item in data.get('targetLogVOS', []):
                    bid_info = get_bid_info(item.get('bidPdFieldId', ''))
                    a = f'''
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
                    </tr>'''

                    target_rows += a

                content = f'''
                <div>
                    <div>
                        <div>
                            <div>
                                <div>
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
                                                1、供应商基本资格条件
                                                （1）具有独立承担民事责任的能力；
                                                （2）具有履行合同所必需的设备和专业技术能力；
                                                （3）具有良好的商业信誉和健全的财务会计制度；
                                                （4）有依法缴纳税收和社会保障资金的良好记录；
                                                （5）近三年内，在经营活动中没有重大违法记录；
                                                （6）法律、行政法规规定的其他条件；
                                                2、供应商特定资格条件：/
                                                3、单位负责人为同一人或者存在直接控股、管理关系的不同投标人，不得参加本项目同一合同项下的竞价活动。
                                                4、本次竞价不接受联合体。
                                                </td>
                                            </tr>
                                            <tr>
                                                <td rowspan="1" colspan="1">报名时间</td>
                                                <td rowspan="1" colspan="3">
                                                    <div>
                                                        <p>开始时间：{data.get('suTime', '')}</p>
                                                        <p>截止时间：{data.get('byTime', '')}</p>
                                                    </div>
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
                                                <td rowspan="1" colspan="1">不限</td>
                                                <td rowspan="1" colspan="1">竞价时间</td>
                                                <td rowspan="1" colspan="1">
                                                    <div>
                                                        <p>开始时间：{data.get('startTime', '')}</p>
                                                        <p>截止时间：{data.get('endTime', '')}</p>
                                                    </div>
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
                                </div>
                            </div>
                        </div>
                    </div>
                    <div>
                        <p>标的信息</p>
                        <div>
                            <div>
                                <div>
                                    <div>
                                        <table>
                                            <thead>
                                                <tr>
                                                    <th colspan="1" rowspan="1">包号</th>
                                                    <th colspan="1" rowspan="1">包名</th>
                                                    <th colspan="1" rowspan="1">品目名称</th>
                                                    <th colspan="1" rowspan="1">数量</th>
                                                    <th colspan="1" rowspan="1">单位</th>
                                                    <th colspan="1" rowspan="1">采购预算(元)</th>
                                                    <th colspan="1" rowspan="1">采购限价(元)</th>
                                                    <th colspan="1" rowspan="1">采购需求</th>
                                                    <th colspan="1" rowspan="1">备注</th>
                                                </tr>
                                            </thead>
                                        </table>
                                    </div>
                                    <div>
                                        <table>
                                            <tbody>
                                                {target_rows}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                    '''
                return content
            elif beToType == 1:
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
                            							<p>{item.get('yearUsage', '')}</p>
                            						</div>
                            					</td>
                            					<td rowspan="1" colspan="1">
                            						<div>
                            							<p>{item.get('buyingLeads', '')}</p>
                            						</div>
                            					</td>
                            					<td rowspan="1" colspan="1">
                            						<div>
                            							<p>{item.get('useDepartment', '')}</p>
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
                            					1. 具有独立承担民事责任的能力（如国家另有规定的，则从其规定。如供应商为分支机构，须取得具有法人资格的总公司（总所）出具给分支机构的授权书，并提供总公司（总所）和分支机构的营业执照（执业许可证）复印件，已由总公司（总所）授权的，总公司（总所）取得的相关资质证书对分支机构有效，法律法规或者行业另有规定的除外）；
                                                2. 参加本项目采购活动前三年内，在经营活动中没有重大违法记录；
                                                3. 在响应截止时间前未被列入失信被执行人、重大税收违法案件当事人名单，未被列入政府采购严重违法失信行为记录名单；
                                                4. 法律、行政法规规定的其他条件。
                                                5. 单位负责人为同一人或者存在直接控股、管理关系的不同供应商，不得参加本项目同一合同项下的采购活动。
                                                6. 供应商须为中国境内合法注册的律师事务所，具有律师事务所执业许可证并经年检合格。
                                                7. 本项目为广东省政府集中采购目录内项目，后续将在广东省政府云平台完成采购工作，供应商须在提交响应文件前完成广东省政府云平台备案工作并提供响应佐证资料。
                                                8.本次采购不接受联合体响应。
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
                            					<p>{data.get('whetherPdName', '')}</p>
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
                            					<p>开始时间：{data.get('suTime', '')}（北京时间）</p>
                            					<p>截止时间：{data.get('byTime', '')}（北京时间）</p>
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
                            					<p>{data.get('obTime', '')}（北京时间）</p>
                            				</div>
                            			</td>
                            			<td rowspan="1" colspan="1">
                            				<div>
                            					<p>开标地点</p>
                            				</div>
                            			</td>
                            			<td rowspan="1" colspan="1">
                            				<div>
                            					<p>{data.get('otherUrl', '')}</p>
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
                            <p>标的信息</p>
                            <div>
                            	<div>
                            		<table>
                            			<thead>
                            				<tr>
                            					<th rowspan="1" colspan="1">
                            						<div><span>包号</span></div>
                            					</th>
                            					<th rowspan="1" colspan="1">
                            						<div><span>包名</span></div>
                            					</th>
                            					<th rowspan="1" colspan="1">
                            						<div><span>品目名称</span></div>
                            					</th>
                            					<th rowspan="1" colspan="1">
                            						<div><span>数量</span></div>
                            					</th>
                            					<th rowspan="1" colspan="1">
                            						<div><span>单位</span></div>
                            					</th>
                            					<th rowspan="1" colspan="1">
                            						<div><span>采购预算(元)</span></div>
                            					</th>
                            					<th rowspan="1" colspan="1">
                            						<div><span>采购限价(元)</span></div>
                            					</th>
                            					<th rowspan="1" colspan="1">
                            						<div><span>采购需求</span></div>
                            					</th>
                            					<th rowspan="1" colspan="1">
                            						<div><span>使用科室</span></div>
                            					</th>
                            					<th rowspan="1" colspan="1">
                            						<div><span>备注</span></div>
                            					</th>
                            				</tr>
                            			</thead>
                            			<tbody>
                            {rows}			</tbody>
                            		</table>
                            	</div>
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
                									<p>{item.get('catalogNumber', '')}</p>
                								</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('directoryName', '')}</p>
                								</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('limitPrice', '')}</p>
                								</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('useDepartment', '')}</p>
                								</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('finalistsNum', '')}</p>
                								</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('domesticNumber', '')}</p>
                								</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('importersNumber', '')}</p>
                								</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('supplyPeriod', '')}</p>
                								</div>
                							</td>
                							<td rowspan="1" colspan="1">
                								<div>
                									<p>{item.get('remarks', '')}</p>
                								</div>
                							</td>
                						</tr>"""
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
                					<p>供应商资格要求：
                                    3.1 在中华人民共和国境内注册，具备独立法人资格，近三个月内依法缴纳税收和社会保障资金。
                                    3.2 所投耗材生产或经营纳入行政管理的，供应商须具有相应的生产或经营许可证（如医疗器械生产或经营备案凭证、医疗器械生产或经营许可证、生产企业卫生许可证等）。
                                    3.3 所投耗材纳入行政管理的，耗材须具有相应的备案凭证或注册证（如医疗器械备案凭证、医疗器械注册证、卫生许可批件、消毒产品安全性评价报告等）。
                                    3.4 所报耗材属于广东省或广州市医用耗材交易平台挂网交易品种（提供挂网证明）；
                                    3.5 单位负责人为同一人或者存在控股、管理关系的不同单位，不得同时参加同一包号的申请，否则均取消本项目的入围资格。
                                    3.6 与采购人存在利害关系可能影响入围公正性的法人、其他组织或者个人，不得申请。
                                    3.7 在截止时间前被“信用中国”网站列入失信被执行人或重大税收违法案件当事人名单的、或被“中国政府采购网”网站列入政府采购严重违法失信行为记录名单（处罚期限尚未届满的）的单位，不得申请。
                                    3.8 本项目不接受联合体申请。
                                    3.9符合法律、行政法规规定的其他条件。</p>
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
                					<p>{data.get('whetherPdName', '')}</p>
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
                					<p>开始时间：{data.get('suTime', '')}</p>
                					<p>截止时间：{data.get('byTime', '')}</p>
                				</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p><mark>开标</mark>时间</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>{data.get('obTime', '')}</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p><mark>开标</mark>地点</p>
                				</div>
                			</td>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p>{data.get('otherUrl', '')}</p>
                				</div>
                			</td>
                		</tr>
                		<tr>
                			<td rowspan="1" colspan="1">
                				<div>
                					<p><mark>采购</mark>人</p>
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
                					<p>{data.get('operationRemarks', '')}</p>
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
                																			<th colspan="1" rowspan="1"><div>包号</div></th>
                																			<th colspan="1" rowspan="1"><div>包名</div></th>
                																			<th colspan="1" rowspan="1"><div>目录序号</div></th>
                																			<th colspan="1" rowspan="1"><div>目录名称</div></th>
                																			<th colspan="1" rowspan="1"><div>采购限价(元)</div></th>
                																			<th colspan="1" rowspan="1"><div>使用科室</div></th>
                																			<th colspan="1" rowspan="1"><div>入围数量</div></th>
                																			<th colspan="1" rowspan="1"><div>国产品牌数量</div></th>
                																			<th colspan="1" rowspan="1"><div>进口品牌数量</div></th>
                																			<th colspan="1" rowspan="1"><div>供应期</div></th>
                																			<th colspan="1" rowspan="1"><div>其他(限价单位等)</div></th>
                																		</tr>
                																	</thead>
                																	<tbody>
                {rows}
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
                						</div>
                					</div>
                				</div>
                			</div>
                		</div>
                	</div>
                </div>
                    """
                return content
            else:
                return ''

        if t == 3:
            if beToType == 11:
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
                                <div>{data.get('projectType', '')}</div>
                            </td>
                            <td rowspan="1" colspan="1">
                                <div>竞标方式</div>
                            </td>
                            <td rowspan="1" colspan="1">
                                <div>{data.get('bidModel', '')}</div>
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
                                <div>{data.get('pcontacts', '')}</div>
                            </td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">
                                <div>联系电话</div>
                            </td>
                            <td rowspan="1" colspan="1">
                                <div>{data.get('pcontactsPhone', '')}</div>
                            </td>
                            <td rowspan="1" colspan="1">
                                <div>联系地址</div>
                            </td>
                            <td rowspan="1" colspan="1">
                                <div>{data.get('paddress', '')}</div>
                            </td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">
                                <div>撤项/流标原因</div>
                            </td>
                            <td rowspan="1" colspan="3">
                                <div>{data.get('operationRemarks', '')}</div>
                            </td>
                        </tr>
                    </tbody>
                </table>
                    """
                return content

            elif beToType == 2:
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
                                            							<p>{item.get('yearUsage', '')}</p>
                                            						</div>
                                            					</td>
                                            					<td rowspan="1" colspan="1">
                                            						<div>
                                            							<p>{item.get('buyingLeads', '')}</p>
                                            						</div>
                                            					</td>
                                            					<td rowspan="1" colspan="1">
                                            						<div>
                                            							<p>{item.get('useDepartment', '')}</p>
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
                                            					1. 具有独立承担民事责任的能力（如国家另有规定的，则从其规定。如供应商为分支机构，须取得具有法人资格的总公司（总所）出具给分支机构的授权书，并提供总公司（总所）和分支机构的营业执照（执业许可证）复印件，已由总公司（总所）授权的，总公司（总所）取得的相关资质证书对分支机构有效，法律法规或者行业另有规定的除外）；
                                                                2. 参加本项目采购活动前三年内，在经营活动中没有重大违法记录；
                                                                3. 在响应截止时间前未被列入失信被执行人、重大税收违法案件当事人名单，未被列入政府采购严重违法失信行为记录名单；
                                                                4. 法律、行政法规规定的其他条件。
                                                                5. 单位负责人为同一人或者存在直接控股、管理关系的不同供应商，不得参加本项目同一合同项下的采购活动。
                                                                6. 供应商须为中国境内合法注册的律师事务所，具有律师事务所执业许可证并经年检合格。
                                                                7. 本项目为广东省政府集中采购目录内项目，后续将在广东省政府云平台完成采购工作，供应商须在提交响应文件前完成广东省政府云平台备案工作并提供响应佐证资料。
                                                                8.本次采购不接受联合体响应。
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
                                            					<p>{data.get('whetherPdName', '')}</p>
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
                                            					<p>开始时间：{data.get('suTime', '')}（北京时间）</p>
                                            					<p>截止时间：{data.get('byTime', '')}（北京时间）</p>
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
                                            					<p>{data.get('obTime', '')}（北京时间）</p>
                                            				</div>
                                            			</td>
                                            			<td rowspan="1" colspan="1">
                                            				<div>
                                            					<p>开标地点</p>
                                            				</div>
                                            			</td>
                                            			<td rowspan="1" colspan="1">
                                            				<div>
                                            					<p>{data.get('otherUrl', '')}</p>
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
                                            <p>标的信息</p>
                                            <div>
                                            	<div>
                                            		<table>
                                            			<thead>
                                            				<tr>
                                            					<th rowspan="1" colspan="1">
                                            						<div><span>包号</span></div>
                                            					</th>
                                            					<th rowspan="1" colspan="1">
                                            						<div><span>包名</span></div>
                                            					</th>
                                            					<th rowspan="1" colspan="1">
                                            						<div><span>品目名称</span></div>
                                            					</th>
                                            					<th rowspan="1" colspan="1">
                                            						<div><span>数量</span></div>
                                            					</th>
                                            					<th rowspan="1" colspan="1">
                                            						<div><span>单位</span></div>
                                            					</th>
                                            					<th rowspan="1" colspan="1">
                                            						<div><span>采购预算(元)</span></div>
                                            					</th>
                                            					<th rowspan="1" colspan="1">
                                            						<div><span>采购限价(元)</span></div>
                                            					</th>
                                            					<th rowspan="1" colspan="1">
                                            						<div><span>采购需求</span></div>
                                            					</th>
                                            					<th rowspan="1" colspan="1">
                                            						<div><span>使用科室</span></div>
                                            					</th>
                                            					<th rowspan="1" colspan="1">
                                            						<div><span>备注</span></div>
                                            					</th>
                                            				</tr>
                                            			</thead>
                                            			<tbody>
                                            {rows}			</tbody>
                                            		</table>
                                            	</div>
                                            </div>
                                                """
                return content

            elif beToType == 12:
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
                                <div>{data.get('projectLocation', '')}</div>
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
                                <div>公告方式</div>
                            </td>
                            <td rowspan="1" colspan="1">
                                <div>{data.get('bidModelName', '')}</div>
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
                                <div>{data.get('purchaserConcat', '')}</div>
                            </td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">
                                <div>联系电话</div>
                            </td>
                            <td rowspan="1" colspan="1">
                                <div>{data.get('purchaserConcatPhone', '')}</div>
                            </td>
                            <td rowspan="1" colspan="1">
                                <div>联系地址</div>
                            </td>
                            <td rowspan="1" colspan="1">
                                <div>{data.get('purchaserAddress', '')}</div>
                            </td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">
                                <div>撤项原因</div>
                            </td>
                            <td rowspan="1" colspan="3">
                                <div>{data.get('releaseRemarks', '')}</div>
                            </td>
                        </tr>
                    </tbody>
                </table>
                    """
                return content

            else:
                return ''

        if t == 4:
            if beToType == 11:
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
                                <div>{data.get('projectType', '')}</div>
                            </td>
                            <td rowspan="1" colspan="1">
                                <div>竞标方式</div>
                            </td>
                            <td rowspan="1" colspan="1">
                                <div>{data.get('bidModel', '')}</div>
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
                                <div>{data.get('pcontacts', '')}</div>
                            </td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">
                                <div>联系电话</div>
                            </td>
                            <td rowspan="1" colspan="1">
                                <div>{data.get('pcontactsPhone', '')}</div>
                            </td>
                            <td rowspan="1" colspan="1">
                                <div>联系地址</div>
                            </td>
                            <td rowspan="1" colspan="1">
                                <div>{data.get('paddress', '')}</div>
                            </td>
                        </tr>
                        <tr>
                            <td rowspan="1" colspan="1">
                                <div>撤项/流标原因</div>
                            </td>
                            <td rowspan="1" colspan="3">
                                <div>{data.get('operationRemarks', '')}</div>
                            </td>
                        </tr>
                    </tbody>
                </table>
                    """
                return content

            elif beToType == 2:
                rows = ""
                for item in data.get('itemHistoryVOList', []):
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
                                									<p>{item.get('catalogNumber', '')}</p>
                                								</div>
                                							</td>
                                							<td rowspan="1" colspan="1">
                                								<div>
                                									<p>{item.get('directoryName', '')}</p>
                                								</div>
                                							</td>
                                							<td rowspan="1" colspan="1">
                                								<div>
                                									<p>{item.get('limitPrice', '')}</p>
                                								</div>
                                							</td>
                                							<td rowspan="1" colspan="1">
                                								<div>
                                									<p>{item.get('useDepartment', '')}</p>
                                								</div>
                                							</td>
                                							<td rowspan="1" colspan="1">
                                								<div>
                                									<p>{item.get('finalistsNum', '')}</p>
                                								</div>
                                							</td>
                                							<td rowspan="1" colspan="1">
                                								<div>
                                									<p>{item.get('domesticNumber', '')}</p>
                                								</div>
                                							</td>
                                							<td rowspan="1" colspan="1">
                                								<div>
                                									<p>{item.get('importersNumber', '')}</p>
                                								</div>
                                							</td>
                                							<td rowspan="1" colspan="1">
                                								<div>
                                									<p>{item.get('supplyPeriod', '')}</p>
                                								</div>
                                							</td>
                                							<td rowspan="1" colspan="1">
                                								<div>
                                									<p>{item.get('remarks', '')}</p>
                                								</div>
                                							</td>
                                						</tr>"""
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
                                					<p>供应商资格要求：
                                                    3.1 在中华人民共和国境内注册，具备独立法人资格，近三个月内依法缴纳税收和社会保障资金。
                                                    3.2 所投耗材生产或经营纳入行政管理的，供应商须具有相应的生产或经营许可证（如医疗器械生产或经营备案凭证、医疗器械生产或经营许可证、生产企业卫生许可证等）。
                                                    3.3 所投耗材纳入行政管理的，耗材须具有相应的备案凭证或注册证（如医疗器械备案凭证、医疗器械注册证、卫生许可批件、消毒产品安全性评价报告等）。
                                                    3.4 所报耗材属于广东省或广州市医用耗材交易平台挂网交易品种（提供挂网证明）；
                                                    3.5 单位负责人为同一人或者存在控股、管理关系的不同单位，不得同时参加同一包号的申请，否则均取消本项目的入围资格。
                                                    3.6 与采购人存在利害关系可能影响入围公正性的法人、其他组织或者个人，不得申请。
                                                    3.7 在截止时间前被“信用中国”网站列入失信被执行人或重大税收违法案件当事人名单的、或被“中国政府采购网”网站列入政府采购严重违法失信行为记录名单（处罚期限尚未届满的）的单位，不得申请。
                                                    3.8 本项目不接受联合体申请。
                                                    3.9符合法律、行政法规规定的其他条件。</p>
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
                                					<p>{data.get('whetherPdName', '')}</p>
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
                                					<p>开始时间：{data.get('suTime', '')}</p>
                                					<p>截止时间：{data.get('byTime', '')}</p>
                                				</div>
                                			</td>
                                		</tr>
                                		<tr>
                                			<td rowspan="1" colspan="1">
                                				<div>
                                					<p><mark>开标</mark>时间</p>
                                				</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>
                                					<p>{data.get('obTime', '')}</p>
                                				</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>
                                					<p><mark>开标</mark>地点</p>
                                				</div>
                                			</td>
                                			<td rowspan="1" colspan="1">
                                				<div>
                                					<p>{data.get('otherUrl', '')}</p>
                                				</div>
                                			</td>
                                		</tr>
                                		<tr>
                                			<td rowspan="1" colspan="1">
                                				<div>
                                					<p><mark>采购</mark>人</p>
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
                                					<p>{data.get('operationRemarks', '')}</p>
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
                                																			<th colspan="1" rowspan="1"><div>包号</div></th>
                                																			<th colspan="1" rowspan="1"><div>包名</div></th>
                                																			<th colspan="1" rowspan="1"><div>目录序号</div></th>
                                																			<th colspan="1" rowspan="1"><div>目录名称</div></th>
                                																			<th colspan="1" rowspan="1"><div>采购限价(元)</div></th>
                                																			<th colspan="1" rowspan="1"><div>使用科室</div></th>
                                																			<th colspan="1" rowspan="1"><div>入围数量</div></th>
                                																			<th colspan="1" rowspan="1"><div>国产品牌数量</div></th>
                                																			<th colspan="1" rowspan="1"><div>进口品牌数量</div></th>
                                																			<th colspan="1" rowspan="1"><div>供应期</div></th>
                                																			<th colspan="1" rowspan="1"><div>其他(限价单位等)</div></th>
                                																		</tr>
                                																	</thead>
                                																	<tbody>
                                {rows}
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
                                						</div>
                                					</div>
                                				</div>
                                			</div>
                                		</div>
                                	</div>
                                </div>
                                    """
                return content

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
