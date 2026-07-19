# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import json


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
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://wssp.hainan.gov.cn",
    "Pragma": "no-cache",
    "Referer": "https://wssp.hainan.gov.cn/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
COOKIES = {
    "JSESSIONID": "46A38A4109E9C83F181BFC65D48AB1E3",
    "yitihua20220424": "42557677"
}


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 需求公示
            {
                "url": "https://wssp.hainan.gov.cn/hainanEdiary/taiji/CaiGouGongShiController.do?reqCode=AjaxInit",
                "page_number": 3,
                'data': {
                    "pageSize": "10",
                    "currentPage": "2",
                    "cgfb_xmmc": "",
                    "cgfb_fwlx": "",
                    "cgfb_bmkssj_start": "",
                    "cgfb_bmjzsj_end": ""
                },
                't': 1
            },
            # 中选公示
            {
                "url": "https://wssp.hainan.gov.cn/hainanEdiary/taiji/ZhongXuanGongShiController.do?reqCode=AjaxInit",
                "page_number": 15,
                'data': {
                    "pageSize": "10",
                    "currentPage": "2",
                    "cgfb_xmmc": "",
                    "cgfb_fwlx": "",
                    "zxxx_ctime_start": "",
                    "zxxx_ctime_end": "",
                    "jzjg_jgmc": "",
                },
                't': 2
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                p['data']['currentPage'] = str(index)
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy(), 't': p['t']
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        resp = auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES, data=params['data'])
        if 400 <= resp.status_code <= 599:
            return ret_list

        data = resp.json().get('dataMap').get('dateList')

        if params['t'] == 1:
            rows = json.loads(data)

            for row in rows:
                cgfb_id = row.get('cgfb_id')
                url = f"https://wssp.hainan.gov.cn/hainanEdiary/taiji/CaiGouGongShiController.do?reqCode=goCgfbDetail&cgfb_id={cgfb_id}"
                if not is_same_origin_url(url, params['url']):
                    continue

                title = row.get('cgfb_xmmc')
                pubTime = row.get('cgfb_bmkssj')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, "cgfb_id": cgfb_id, 't': params['t']})
        if params['t'] == 2:
            rows = data

            for row in rows:
                zxxx_id = row.get('zxxx_id')
                url = f"https://wssp.hainan.gov.cn/hainanEdiary/taiji/ZhongXuanGongShiController.do?reqCode=goZxxxDetail&zxxx_id={zxxx_id}"
                if not is_same_origin_url(url, params['url']):
                    continue

                title = row.get('cgfb_xmmc')
                pubTime = row.get('cgfb_bmjzsj')
                cgfb_id = row.get('cgfb_id')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, "zxxx_id": zxxx_id, 't': params['t'], 'cgfb_id': cgfb_id})

        return ret_list

    def get_content(self, params: dict):
        url = "https://wssp.hainan.gov.cn/hainanEdiary/taiji/CaiGouGongShiController.do?reqCode=CgfbDetail"
        payload = {"cgfb_id": params['cgfb_id']} if params['t'] == 1 else {"zxxx_id": params['zxxx_id']}

        resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES, data=payload)
        if 400 <= resp.status_code <= 599:
            return None

        data = resp.json().get('dataMap')
        content = self.render_content(data, params['t'])

        url = "https://wssp.hainan.gov.cn/hainanEdiary/taiji/CaiGouGongShiController.do?reqCode=fileList"
        payload = {"cgfb_id": params['cgfb_id']}
        resp = auto_request(url=url, headers=HEADERS, cookies=COOKIES, data=payload)
        if 400 <= resp.status_code <= 599:
            content += ""
        else:
            data_list = resp.json().get('dataMap').get('dateList')
            for item in data_list:
                href = f"https://wssp.hainan.gov.cn/hainanEdiary/taiji/HnZjfwFileEditController.do?reqCode=fileDownLoad&file_id={item.get('file_id')}&signature={item.get('signature')}"
                a_tag = f'<a href="{href}">{item.get("file_xsmc")}</a>'
                content += a_tag

        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}

    def render_content(self, data, t):
        if t == 1:
            content = f"""
                <table>
                <tr>
                    <th>报名截止时间</th>
                    <td>{data.get('cgfb_bmjzsj', '')}</td>
                    <th>参加报名中介数</th>
                    <td>{data.get('cgfb_jg_bms', '')}</td>
                </tr>
                <tr>
                    <th>服务需求名称</th>
                    <td>{data.get('cgfb_xmmc', '')}</td>
                    <th>选取中介方式</th>
                    <td>{data.get('cgfb_xqfs_Code', '')}</td>
                </tr>
                <tr>
                    <th>资金来源</th>
                    <td colspan="3">{data.get('cgfb_zjly', '')}</td>
                </tr>
                <tr>
                    <th>发布时间</th>
                    <td>{data.get('cgfb_fbsj', '')}</td>
                    <th>服务需求编号</th>
                    <td>{data.get('cgfb_fwcgbh', '')}</td>
                </tr>
                <tr>
                    <th>项目业主名称</th>
                    <td>{data.get('cgfb_yzdw_jgmc', '')}</td>
                    <th>所属项目所在地</th>
                    <td>{data.get('cgfb_xmszd', '')}</td>
                </tr>
                <tr>
                    <th>所属项目总投资</th>
                    <td>{data.get('cgfb_xmztz', '')}（万元）</td>
                    <th>事项名称</th>
                    <td>{data.get('cgfb_sxmc', '')}</td>
                </tr>
                <tr>
                    <th>对应的投资审批事项</th>
                    <td>{data.get('tzspsx', '')}</td>
                    <th>事项审批部门</th>
                    <td>{data.get('zjfwsx_spbm_Code', '')}</td>
                </tr>
                <tr>
                    <th>资质要求</th>
                    <td>{data.get('zjfwsx_zzlx_Code', '')}</td>
                    <th>等级</th>
                    <td>{data.get('cgfb_zzdj_Code', '')}</td>
                </tr>
                <tr>
                    <th>服务金额</th>
                    <td>下限{data.get('cgfb_fwje', '')}（元） ,上限{data.get('cgfb_fwje_end', '')}（元）</td>
                    <th>服务时限</th>
                    <td>下限{data.get('cgfb_fwsx', '')}（天） ,上限{data.get('cgfb_fwsx_end', '')}（天）</td>
                </tr>
                <tr>
                    <th>服务内容</th>
                    <td colspan="3">{data.get('cgfb_fwnr', '')}</td>
                </tr>
                <tr>
                    <th>选取时间</th>
                    <td>{data.get('cgfb_xqsj', '')} 至 {data.get('cgfb_xqjz', '')}</td>
                    <th>报名日期</th>
                    <td>{data.get('cgfb_bmkssj', '')} 至 {data.get('cgfb_bmjzsj', '')}</td>
                </tr>
                <tr>
                    <th>咨询电话</th>
                    <td>{data.get('yzdw_dh', '')}</td>
                    <th>备注</th>
                    <td colspan="3">{data.get('cgfb_bz', '')}</td>
                </tr>
                <tr></tr>
            </table>
                """
            return content
        if t == 2:
            content = f"""
                <table>
            	<tr>
            		<th>中选机构名称</th>
            		<td>{data.get('jzjg_jgmc', '')}</td>
            		<th>中选金额(元)</th>
            		<td>{data.get('zxxx_je', '')}</td>
            	</tr>
            	<tr>
            		<th>报名截止时间</th>
            		<td>{data.get('cgfb_bmjzsj', '')}</td>
            		<th>参加报名中介数</th>
            		<td>{data.get('cgfb_jg_bms', '')}</td>
            	</tr>
            	<tr>
            		<th>服务需求名称</th>
            		<td>{data.get('cgfb_xmmc', '')}</td>
            		<th>选取中介方式</th>
            		<td>{data.get('cgfb_xqfs_Code', '')}</td>
            	</tr>
            	<tr>
            		<th>发布时间</th>
            		<td>{data.get('cgfb_fbsj', '')}</td>
            		<th>服务需求编号</th>
            		<td>{data.get('cgfb_fwcgbh', '')}</td>
            	</tr>
            	<tr>
            		<th>项目业主名称</th>
            		<td>{data.get('cgfb_yzdw_jgmc', '')}</td>
            		<th>所属项目所在地</th>
            		<td>{data.get('cgfb_xmszd', '')}</td>
            	</tr>
            	<tr>
            		<th>所属项目总投资</th>
            		<td>{data.get('cgfb_xmztz', '')}（万元）</td>
            		<th>事项名称</th>
            		<td>{data.get('cgfb_sxmc', '')}</td>
            	</tr>
            	<tr>
            		<th>资质要求</th>
            		<td>{data.get('zjfwsx_zzlx_Code', '')}</td>
            		<th>等级</th>
            		<td>{data.get('cgfb_zzdj_Code', '')}</td>
            	</tr>
            	<tr>
            		<th>服务金额</th>
            		<td>下限{data.get('cgfb_fwje', '')}（元） ,上限{data.get('cgfb_fwje_end', '')}（元）</td>
            		<th>服务时限</th>
            		<td>下限{data.get('cgfb_fwsx', '')}（天） ,上限{data.get('cgfb_fwsx_end', '')}（天）</td>
            	</tr>
            	<tr>
            		<th>服务内容</th>
            		<td colspan="3">{data.get('cgfb_fwnr', '')}</td>
            	</tr>
            	<tr>
            		<th>报名日期</th>
            		<td>{data.get('cgfb_bmkssj', '')} 至 {data.get('cgfb_bmjzsj', '')}</td>
            		<th>选取时间</th>
            		<td>{data.get('cgfb_xqsj', '')} 至 {data.get('cgfb_xqjz', '')}</td>
            	</tr>
            	<tr>
            		<th>咨询电话</th>
            		<td>{data.get('yzdw_dh', '')}</td>
            		<th>备注</th>
            		<td colspan="3">{data.get('cgfb_bz', '')}</td>
            	</tr>
            	<tr>
            		<th>中选服务时限（天）</th>
            		<td colspan="3">{data.get('zxxx_sx', '')}</td>
            	</tr>
            </table>
                """
            return content


if __name__ == "__main__":
    CrawlerObject().start()
