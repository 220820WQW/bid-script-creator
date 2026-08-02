# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from bbSpider import Spider, request, handle_str
import time, base64, io, time, random
import numpy as np
from PIL import Image
from datetime import datetime, timedelta
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


HEADERS = {}
COOKIES = {}


def get_slider_captcha(proxies=None):
    """请求 /sa/gen 直到获取 SLIDER 类型的验证码"""
    resp = request.post(
        'http://221.224.132.154:9093/zhcx/sa/gen',
        json={},
        headers={'Content-Type': 'application/json;charset=UTF-8'},
        proxies=proxies,
    )
    data = resp.json()
    if data['captcha']['type'] == 'SLIDER':
        return data


def find_gap_position(bg_b64, t_b64):
    """通过图像处理找到缺口位置"""
    bg_img = Image.open(io.BytesIO(base64.b64decode(bg_b64)))
    t_img = Image.open(io.BytesIO(base64.b64decode(t_b64)))

    bg_arr = np.array(bg_img.convert('L'), dtype=np.float64)
    t_arr = np.array(t_img.convert('RGBA'), dtype=np.float64)
    t_alpha = t_arr[:, :, 3]

    # 找到模板中非透明区域（滑块拼图块）
    mask = t_alpha > 128
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return None, None, None, None
    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()
    piece_w = x_max - x_min + 1

    # 在背景图的相同Y区域扫描，找缺口
    bg_strip = bg_arr[y_min:y_max + 1, :]

    # 计算每列的平均亮度
    col_mean = np.mean(bg_strip, axis=0)

    # 缺口区域颜色明显不同，找亮度突变的位置
    col_grad = np.abs(np.gradient(col_mean))

    # 找梯度最大的两个峰（缺口的左右边缘）
    peaks = []
    for i in range(1, len(col_grad) - 1):
        if col_grad[i] > col_grad[i - 1] and col_grad[i] > col_grad[i + 1]:
            peaks.append((i, col_grad[i]))
    peaks.sort(key=lambda x: -x[1])

    # 找间距接近 piece_w 且梯度和最大的峰对
    best_pair = None
    best_score = 0
    for i in range(min(30, len(peaks))):
        for j in range(i + 1, min(30, len(peaks))):
            p1, p2 = sorted([peaks[i][0], peaks[j][0]])
            w = p2 - p1
            if abs(w - piece_w) < 12:
                score = peaks[i][1] + peaks[j][1]
                if score > best_score:
                    best_score = score
                    best_pair = (p1, p2)

    if best_pair is None:
        # 回退：用模板匹配
        t_gray = np.array(t_img.convert('L'), dtype=np.float64)
        t_piece = t_gray[y_min:y_max + 1, x_min:x_max + 1]
        best_x = 0
        best_sad = float('inf')
        for x in range(0, bg_arr.shape[1] - piece_w - 1):
            bg_patch = bg_strip[:, x:x + piece_w]
            sad = np.sum(np.abs(bg_patch - t_piece))
            if sad < best_sad:
                best_sad = sad
                best_x = x
        gap_left = best_x
    else:
        gap_left = best_pair[0]

    return gap_left, x_min, y_min, piece_w


def generate_track(target_x, duration_ms=None):
    """生成仿人类滑动轨迹"""
    if duration_ms is None:
        duration_ms = random.randint(800, 1500)

    # 初始延迟：模拟从看到验证码到开始拖动的反应时间
    initial_delay = random.randint(200, 1000)
    track = []
    # down 事件
    track.append({'x': 0, 'y': 0, 'type': 'down', 't': initial_delay})

    # 生成移动轨迹 - 模拟加速-匀速-减速
    current_x = 0
    current_y = 0
    elapsed = initial_delay

    # 分段：加速段(0-30%) -> 匀速段(30-70%) -> 减速段(70-100%)
    while current_x < target_x:
        elapsed += random.randint(4, 12)
        progress = current_x / target_x if target_x > 0 else 0

        if progress < 0.3:
            step = random.uniform(2, 6)
        elif progress < 0.7:
            step = random.uniform(3, 8)
        else:
            step = random.uniform(1, 4)

        current_x = min(current_x + step, target_x)
        # 微小Y轴抖动
        current_y += random.uniform(-1, 1)
        current_y = max(-5, min(5, current_y))

        track.append({
            'x': round(current_x),
            'y': round(current_y),
            'type': 'move',
            't': elapsed,
        })

    # 到达目标位置后短暂停顿（模拟人眼确认）
    elapsed += random.randint(50, 150)

    # up 事件
    track.append({
        'x': round(current_x),
        'y': round(current_y),
        'type': 'up',
        't': elapsed,
    })

    return track, elapsed


def validate_captcha(captcha_id, bg_w, bg_h, start_time, stop_time, track_list, proxies=None, path=None):
    """提交验证码验证"""
    url = 'queryZTBPage' if path is None else path
    payload = {
        'id': captcha_id,
        'data': {
            'bgImageWidth': bg_w,
            'bgImageHeight': bg_h,
            'startTime': start_time,
            'stopTime': stop_time,
            'trackList': track_list,
        },
    }
    resp = request.post(
        f'http://221.224.132.154:9093/zhcx/sa/check/{url}',
        json=payload,
        headers={'Content-Type': 'application/json;charset=UTF-8'},
        proxies=proxies,
    )
    return resp.json()


def get_token(path=None):
    # Step 1: 获取 SLIDER 验证码
    for _ in range(20):
        proxies = agent_pool("http://zhcx.zfcjj.suzhou.gov.cn:81/")['https']
        captcha_data = get_slider_captcha(proxies)
        if captcha_data:
            break
        time.sleep(1)
    else:
        return None

    captcha_id = captcha_data['id']
    cap = captcha_data['captcha']

    # Step 2: 找缺口位置
    bg_b64 = cap['backgroundImage'].split(',')[1]
    t_b64 = cap['templateImage'].split(',')[1]
    gap_left, piece_off_x, piece_off_y, piece_w = find_gap_position(bg_b64, t_b64)

    if gap_left is None:
        return None

    # 计算目标拖动距离
    target_x = gap_left - piece_off_x

    # Step 3: 生成轨迹
    track_list, duration = generate_track(target_x)
    # stop_time 记录为当前时间，start_time 根据轨迹时长反推
    # 确保 stopTime - startTime ≈ trackList 最后 t 值
    stop_dt = datetime.utcnow()
    start_dt = stop_dt - timedelta(milliseconds=duration)
    start_time = start_dt.isoformat() + 'Z'
    stop_time = stop_dt.isoformat() + 'Z'

    # Step 4: 验证
    result = validate_captcha(
        captcha_id,
        int(cap['backgroundImageWidth']),
        int(cap['backgroundImageHeight']),
        start_time,
        stop_time,
        track_list,
        proxies=proxies,
        path=path
    )

    # Step 5: 如果成功，获取数据
    if result.get('code') == 200:
        token = result['data']['id']
        print(f'Token: {token}')
        return token, proxies
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
            # 招标信息
            {
                "url": "http://221.224.132.154:9093/zhcx/dataSearch/queryZTBPage",
                "page_number": 5,
                'data': {
                    "t": "1785286439628",
                    "projectname": "",
                    "projectlocation": "",
                    "projectowner": "",
                    "startdate": "",
                    "enddate": "",
                    "limit": "10",
                    "page": "2"
                },
                't': 1,
                'path': "queryZTBPage"
            },
            # 招标信息
            {
                "url": "http://221.224.132.154:9093/zhcx/dataSearch/queryZBPage",
                "page_number": 5,
                'data': {
                    "t": "1785290067858",
                    "projectname": "",
                    "projectlocation": "",
                    "projectowner": "",
                    "projectwin": "",
                    "startdate": "",
                    "enddate": "",
                    "limit": "10",
                    "page": "2"
                },
                't': 2,
                'path': "queryZBPage"
            },

            # 项目登记
            {
                "url": "http://221.224.132.154:9093/zhcx/dataSearch/queryLXDJPage",
                "page_number": 5,
                'data': {
                    "t": "1785291421087",
                    "projectname": "",
                    "projectlocation": "",
                    "projectowner": "",
                    "limit": "10",
                    "page": "2"
                },
                't': 3,
                'path': "queryLXDJPage"
            },

            # 合同信息
            {
                "url": "http://221.224.132.154:9093/zhcx/dataSearch/queryHTBAPage",
                "page_number": 10,
                'data': {
                    "t": "1785292103961",
                    "projectname": "",
                    "projectlocation": "",
                    "projectowner": "",
                    "startdate": "",
                    "enddate": "",
                    "limit": "10",
                    "page": "10"
                },
                't': 4,
                'path': "queryHTBAPage"
            },
            # 合同变更备案
            {
                "url": "http://221.224.132.154:9093/zhcx/dataSearch/queryHTBGPage",
                "page_number": 5,
                'data': {
                    "t": "1785293113871",
                    "projectname": "",
                    "projectowner": "",
                    "projectamount": "",
                    "startdate": "",
                    "enddate": "",
                    "startdate2": "",
                    "enddate2": "",
                    "limit": "10",
                    "page": "5"
                },
                't': 5,
                'path': "queryHTBGPage"
            },
            # 施工许可
            {
                "url": "http://221.224.132.154:9093/zhcx/dataSearch/querySGXKPage",
                "page_number": 5,
                'data': {
                    "t": "1785293540889",
                    "projectname": "",
                    "projectlocation": "",
                    "projectowner": "",
                    "projectbuild": "",
                    "startdate": "",
                    "enddate": "",
                    "limit": "10",
                    "page": "10"
                },
                't': 6,
                'path': "querySGXKPage"
            },
            # 质量监督
            {
                "url": "http://221.224.132.154:9093/zhcx/dataSearch/queryZLJDPage",
                "page_number": 1,
                'data': {
                    "t": "1785294267427",
                    "projectname": "",
                    "projectowner": "",
                    "startdate": "",
                    "enddate": "",
                    "limit": "10",
                    "page": "1"
                },
                't': 7,
                'path': "queryZLJDPage"
            },
            # 安全监督
            {
                "url": "http://221.224.132.154:9093/zhcx/dataSearch/queryAQJDPage",
                "page_number": 1,
                'data': {
                    "t": "1785294865267",
                    "projectname": "",
                    "projectowner": "",
                    "startdate": "",
                    "enddate": "",
                    "limit": "10",
                    "page": "1"
                },
                't': 8,
                'path': "queryAQJDPage"
            },
            # 竣工备案
            {
                "url": "http://221.224.132.154:9093/zhcx/dataSearch/queryJGBAPage",
                "page_number": 1,
                'data': {
                    "t": "1785295159130",
                    "projectname": "",
                    "finishnum": "",
                    "qualitynum": "",
                    "startdate": "",
                    "enddate": "",
                    "limit": "10",
                    "page": "1"
                },
                't': 9,
                'path': "queryJGBAPage"
            },
            # 城建档案
            {
                "url": "http://221.224.132.154:9093/zhcx/dataSearch/queryCJDAPage",
                "page_number": 1,
                'data': {
                    "t": "1785295626754",
                    "projectname": "",
                    "projectlocation": "",
                    "projectowner": "",
                    "approvecert": "",
                    "projecttype": "",
                    "limit": "10",
                    "page": "1"
                },
                't': 10,
                'path': "queryCJDAPage"
            },

        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                p['data']['page'] = str(index)
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy(), 't': p['t'], 'path': p['path']
                    }
                )

    def get_list(self, params: dict):
        ret_list = []

        try:
            token, proxies = get_token(params['path'])
        except:
            return ret_list

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'token': token,
        }

        params['data']['t'] = str(int(time.time() * 1000))
        resp = request.post(url=params['url'], headers=headers, cookies=COOKIES, data=params['data'], proxies=proxies)
        if 400 <= resp.status_code <= 599:
            return ret_list

        try:
            data = resp.json().get('page')
            rows = data.get('list')
        except:
            return ret_list

        url_map = {
            1: "http://zhcx.zfcjj.suzhou.gov.cn:81/zhcx/detail.html?id={}&type=xmztb",
            2: "http://zhcx.zfcjj.suzhou.gov.cn:81/zhcx/detail.html?id={}&type=zhongbiao",
            3: "http://zhcx.zfcjj.suzhou.gov.cn:81/zhcx/detail.html?id={}&type=lxdj",
            4: "http://zhcx.zfcjj.suzhou.gov.cn:81/zhcx/detail.html?id={}&type=htba",
            5: "http://zhcx.zfcjj.suzhou.gov.cn:81/zhcx/detail.html?id={}&type=htbabg",
            6: "http://zhcx.zfcjj.suzhou.gov.cn:81/zhcx/detail.html?id={}&type=sgxk",
            7: "http://zhcx.zfcjj.suzhou.gov.cn:81/zhcx/detail.html?id={}&type=zljdNew",
            8: "http://zhcx.zfcjj.suzhou.gov.cn:81/zhcx/detail.html?id={}&type=aqjdNew",
            9: "http://zhcx.zfcjj.suzhou.gov.cn:81/zhcx/detail.html?id={}&type=jgba",
            10: "http://zhcx.zfcjj.suzhou.gov.cn:81/zhcx/detail.html?id={}&type=cjda"
        }

        if params['t'] in [1, 2]:
            for row in rows:
                id = row.get('id')
                url = url_map[params['t']].format(id)

                title = row.get('projectName')
                pubTime = row.get('tenderFromDate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 't': params['t']})

        if params['t'] == 3:
            for row in rows:
                id = row.get('id')
                url = url_map[params['t']].format(id)

                title = row.get('prjName')
                pubTime = row.get('tenderFromDate') or datetime.now().strftime('%Y-%m-%d')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 't': params['t']})

        if params['t'] == 4:
            for row in rows:
                id = row.get('uuid')
                url = url_map[params['t']].format(id)

                title = row.get('gcmc')
                pubTime = row.get('barq')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 't': params['t']})

        if params['t'] == 5:
            for row in rows:
                id = row.get('rowguid')
                url = url_map[params['t']].format(id)

                title = row.get('gcname')
                pubTime = row.get('sqdate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 't': params['t']})

        if params['t'] == 6:
            for row in rows:
                id = row.get('guid')
                sgdw = row.get('sgdw')
                url = url_map[params['t']].format(id) + f"&sgdw={sgdw}"

                title = row.get('xmmc')
                pubTime = row.get('fzrq')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 't': params['t'], 'sgdw': sgdw})

        if params['t'] in [7, 8]:
            for row in rows:
                id = row.get('projectRegNo')
                url = url_map[params['t']].format(id)

                title = row.get('projectName')
                pubTime = row.get('acceptDate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 't': params['t']})

        if params['t'] == 9:
            for row in rows:
                id = row.get('uuid')
                url = url_map[params['t']].format(id)

                title = row.get('xmmc')
                pubTime = row.get('barq')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 't': params['t']})

        if params['t'] == 10:
            for row in rows:
                id = row.get('id')
                url = url_map[params['t']].format(id)

                title = row.get('projectName')
                pubTime = row.get('projectStartDate')
                ret_list.append({'url': url, 'title': title, 'pubTime': pubTime, 'id': id, 't': params['t']})

        return ret_list

    def get_content(self, params: dict):
        try:
            token, proxies = get_token()
        except:
            return None

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'token': token,
        }

        url_map = {
            1: "http://221.224.132.154:9093/zhcx/dataSearch/getZTBDetail",
            2: "http://221.224.132.154:9093/zhcx/dataSearch/getZBDetail",
            3: "http://221.224.132.154:9093/zhcx/dataSearch/getLXDJDetail",
            4: "http://221.224.132.154:9093/zhcx/dataSearch/getHTBADetail",
            5: "http://221.224.132.154:9093/zhcx/dataSearch/getHTBGDetail",
            6: "http://221.224.132.154:9093/zhcx/dataSearch/getSGXKDetail",
            7: "http://221.224.132.154:9093/zhcx/dataSearch/getZLJDDetail",
            8: "http://221.224.132.154:9093/zhcx/dataSearch/getAQJDDetail",
            9: "http://221.224.132.154:9093/zhcx/dataSearch/getJGBADetail",
            10: "http://221.224.132.154:9093/zhcx/dataSearch/getCJDADetail"
        }

        if params['t'] == 4 or params['t'] == 9:
            data = {'uuid': params['id']}
        elif params['t'] == 6:
            data = {'uuid': params['id'], 'sgdw': params['sgdw']}
        else:
            data = {"id": params['id']}

        resp = auto_request(url=url_map[params['t']], headers=headers, cookies=COOKIES, data=data, proxies=proxies)
        if 400 <= resp.status_code <= 599:
            return None

        try:
            data = resp.json().get('entity')
        except:
            return None

        content = self.render_content(data, params['t'])
        content = handle_str.completion_url(str(content), params['url'])

        return {"title": params['title'], "pubTime": params['pubTime'], "url": params['url'], "content": content}

    def render_content(self, data, t):
        if t == 1:
            content = f"""
            <table>
            <tr>
                <td colspan="4"><mark>招标</mark>项目信息</td>
            </tr>
            <tr>
                <td><mark>招标</mark>项目名称：</td>
                <td colspan="3">{data.get('projectName', '')}</td>
            </tr>
            <tr>
                <td><mark>招标</mark>人：</td>
                <td colspan="3">{data.get('constructionCompany', '')}</td>
            </tr>
            <tr>
                <td><mark>招标</mark>代理机构：</td>
                <td>{data.get('agentCompany', '')}</td>
                <td>项目所属地区：</td>
                <td>{data.get('tenderRegion', '')}</td>
            </tr>
            <tr>
                <td>工程地点：</td>
                <td colspan="3">{data.get('projectAddress', '')}</td>
            </tr>
            <tr>
                <td>工程规模：</td>
                <td colspan="3">{data.get('projectSize', '') or ''}</td>
            </tr>
            <tr>
                <td><mark>招标</mark>类型：</td>
                <td>{data.get('tenderType', '')}</td>
                <td>工程性质：</td>
                <td>{data.get('projectType', '')}</td>
            </tr>
            <tr>
                <td colspan="4"><mark>招标</mark>项目标段信息</td>
            </tr>
            <tr>
                <td>序号</td>
                <td>标段（包）名称</td>
                <td><mark>招标</mark>方式</td>
                <td><mark>合同</mark>估算价（万元）</td>
            </tr>
            <tr>
                <td>1</td>
                <td>{data.get('tenderName', '')}</td>
                <td>{data.get('tenderMethod', '')}</td>
                <td>{data.get('tenderInvest', '')}</td>
            </tr>
            <tr>
                <td><mark>公告</mark>开始日期：</td>
                <td>{data.get('tenderFromDate', '')}</td>
                <td><mark>公告</mark>结束日期：</td>
                <td>{data.get('tenderToDate', '')}</td>
            </tr>
        </table>
            """
            return content

        if t == 2:
            content = f"""
                <table>
            	<tr>
            		<td colspan="4"><mark>招标</mark>项目信息</td>
            	</tr>
            	<tr>
            		<td><mark>招标</mark>项目名称：</td>
            		<td colspan="3">{data.get('projectName', '')}</td>
            	</tr>
            	<tr>
            		<td><mark>招标</mark>人：</td>
            		<td colspan="3">{data.get('constructionCompany', '')}</td>
            	</tr>
            	<tr>
            		<td><mark>招标</mark>代理机构：</td>
            		<td colspan="3">{data.get('agentCompany', '')}</td>
            	</tr>
            	<tr>
            		<td colspan="4"><mark>中标</mark>结果信息</td>
            	</tr>
            	<tr>
            		<td><mark>中标</mark>单位：</td>
            		<td>{data.get('tenderCompany', '')}</td>
            		<td><mark>中标</mark>价格（元）：</td>
            		<td>{data.get('tenderMoney', '')}</td>
            	</tr>
            	<tr>
            		<td><mark>中标</mark><mark>工期</mark>（天）：</td>
            		<td>{data.get('tenderDay', '')}</td>
            		<td><mark>中标</mark>质量标准：</td>
            		<td>{data.get('tenderReMark', '') or ''}</td>
            	</tr>
            	<tr>
            		<td><mark>中标</mark>项目负责人：</td>
            		<td colspan="3">{data.get('tenderManager', '')}</td>
            	</tr>
            	<tr>
            		<td colspan="4"><mark>公告</mark>信息</td>
            	</tr>
            	<tr>
            		<td><mark>备案</mark>日期：</td>
            		<td colspan="3">{data.get('tenderTime', '')}</td>
            	</tr>
            </table>
                """
            return content

        if t == 3:
            content = f"""
                <table>
            	<tr>
            		<td>项目名称：</td>
            		<td colspan="3">{data.get('prjName', '')}</td>
            	</tr>
            	<tr>
            		<td>项目编号：</td>
            		<td>{data.get('projectNum', '')}</td>
            		<td>所属地区：</td>
            		<td>{data.get('prjRegion', '')}</td>
            	</tr>
            	<tr>
            		<td>项目类型：</td>
            		<td>{data.get('prjType', '')}</td>
            		<td><mark>立项</mark>文号：</td>
            		<td>{data.get('prjSetupNum', '')}</td>
            	</tr>
            	<tr>
            		<td>建设单位：</td>
            		<td>{data.get('consUnitName', '')}</td>
            		<td>投资额(万元)：</td>
            		<td>{data.get('prjFee', '')}</td>
            	</tr>
            	<tr>
            		<td>工程性质：</td>
            		<td>{data.get('prjProp', '')}</td>
            		<td>工程地址：</td>
            		<td>{data.get('prjAddr', '')}</td>
            	</tr>
            	<tr>
            		<td>计划<mark>开工</mark>时间：</td>
            		<td>{data.get('prjPlanStart', '')}</td>
            		<td>计划<mark>竣工</mark>时间：</td>
            		<td>{data.get('prjPlanEnd', '')}</td>
            	</tr>
            </table>
                """
            return content

        if t == 4:
            content = f"""
                <table>
            	<tr>
            		<td>项目名称：</td>
            		<td colspan="3">{data.get('gcmc', '')}</td>
            	</tr>
            	<tr>
            		<td>项目经理：</td>
            		<td>{data.get('xmjl', '')}</td>
            		<td>项目属地：</td>
            		<td>{data.get('gcsd', '')}</td>
            	</tr>
            	<tr>
            		<td>建设单位：</td>
            		<td>{data.get('fbr', '')}</td>
            		<td>建设单位代码：</td>
            		<td>{data.get('jsdwzzjgdm', '')}</td>
            	</tr>
            	<tr>
            		<td>施工单位：</td>
            		<td>{data.get('cbr', '')}</td>
            		<td>施工单位代码：</td>
            		<td>{data.get('sgdwzzjgdm', '')}</td>
            	</tr>
            	<tr>
            		<td>承包性质：</td>
            		<td>{data.get('cbxzType', '')}</td>
            		<td>工程地点：</td>
            		<td>{data.get('gcdz', '')}</td>
            	</tr>
            	<tr>
            		<td><mark>建筑面积</mark>(平方米)：</td>
            		<td>{data.get('jzmj', '')}</td>
            		<td><mark>合同</mark>价(元)：</td>
            		<td>{data.get('htj', '')}</td>
            	</tr>
            	<tr>
            		<td>计划<mark>开工</mark>时间：</td>
            		<td>{data.get('jhkgrq', '')}</td>
            		<td>计划<mark>竣工</mark>时间：</td>
            		<td>{data.get('jhjgrq', '')}</td>
            	</tr>
            	<tr>
            		<td>归集日期：</td>
            		<td>{data.get('shrq', '')}</td>
            		<td></td>
            		<td></td>
            	</tr>
            </table>
                """
            return content

        if t == 5:
            content = f"""
                <table>
            	<tr>
            		<td>工程名称：</td>
            		<td colspan="3">{data.get('gcname', '')}</td>
            	</tr>
            	<tr>
            		<td><mark>变更</mark><mark>备案</mark>表编号：</td>
            		<td>{data.get('htchangenum', '')}</td>
            		<td>承包商：</td>
            		<td>{data.get('chengbaodw', '')}</td>
            	</tr>
            	<tr>
            		<td><mark>变更</mark><mark>备案</mark>申报日期：</td>
            		<td>{data.get('sqdate', '')}</td>
            		<td>本次<mark>变更</mark>估算金额(元)：</td>
            		<td>{data.get('changemoney', '')}</td>
            	</tr>
            	<tr>
            		<td>累计<mark>变更</mark>估算金额(元)：</td>
            		<td>{data.get('totalchangemoney', '')}</td>
            		<td>累计<mark>变更</mark>额占<mark>合同</mark>价百分比：</td>
            		<td>{data.get('totalpercent', '')}</td>
            	</tr>
            	<tr>
            		<td><mark>变更</mark><mark>备案</mark>性质：</td>
            		<td>{data.get('changetype', '')}</td>
            		<td><mark>变更</mark>内容：</td>
            		<td>{data.get('changecontent', '')}</td>
            	</tr>
            	<tr>
            		<td><mark>变更</mark>原因：</td>
            		<td>{data.get('changereason', '')}</td>
            		<td><mark>备案</mark>日期：</td>
            		<td>{data.get('tgdate', '')}</td>
            	</tr>
            </table>
                """
            return content

        if t == 6:
            content = f"""
                <table>
            	<tr>
            		<td>项目名称：</td>
            		<td colspan="3">{data.get('xmmc', '')}</td>
            	</tr>
            	<tr>
            		<td>项目类型：</td>
            		<td>{data.get('projectlx', '')}</td>
            		<td>建设类型：</td>
            		<td>{data.get('jianslx', '')}</td>
            	</tr>
            	<tr>
            		<td><mark>合同</mark>总造价（万元）：</td>
            		<td>{data.get('tzze', '')}</td>
            		<td>建设规模：</td>
            		<td>{data.get('gcgm', '')}</td>
            	</tr>
            	<tr>
            		<td><mark>建筑面积</mark>(平方米)：</td>
            		<td>{data.get('jsmj', '')}</td>
            		<td>发证日期：</td>
            		<td>{data.get('fzrq', '')}</td>
            	</tr>
            	<tr>
            		<td>建设单位：</td>
            		<td>{data.get('jsdw', '')}</td>
            		<td>施工单位：</td>
            		<td>{data.get('sgdw', '')}</td>
            	</tr>
            </table>
                """
            return content

        if t == 7 or t == 8:
            content = f"""
                <table>
            	<tr>
            		<td>项目名称：</td>
            		<td colspan="3">{data.get('projectName', '')}</td>
            	</tr>
            	<tr>
            		<td>工程注册号：</td>
            		<td>{data.get('regNo', '')}</td>
            		<td>工程所在地：</td>
            		<td>{data.get('projectAddr', '')}</td>
            	</tr>
            	<tr>
            		<td><mark>建筑面积</mark>(平方米)：</td>
            		<td>{data.get('projectSize', '')}</td>
            		<td>工程造价(万元)：</td>
            		<td>{data.get('projectAmount', '')}</td>
            	</tr>
            	<tr>
            		<td>建设单位：</td>
            		<td>{data.get('hostName', '')}</td>
            		<td><mark>质监</mark>机构：</td>
            		<td>{data.get('supervisorName', '')}</td>
            	</tr>
            	<tr>
            		<td>申报人：</td>
            		<td>{data.get('applyName', '')}</td>
            		<td>受理日期：</td>
            		<td colspan="3">{data.get('acceptDate', '')}</td>
            	</tr>
            </table>
                """
            return content

        if t == 9:
            content = f"""
                <table>
            	<tr>
            		<td>项目名称：</td>
            		<td colspan="3">{data.get('prjfinishname', '')}</td>
            	</tr>
            	<tr>
            		<td><mark>竣工</mark><mark>备案</mark>编号：</td>
            		<td>{data.get('prjfinishnum', '')}</td>
            		<td>施工<mark>许可</mark>证号：</td>
            		<td>{data.get('builderlicencenum', '')}</td>
            	</tr>
            	<tr>
            		<td>实际造价(万元)：</td>
            		<td>{data.get('factcost', '')}</td>
            		<td>实际面积(平方米)：</td>
            		<td>{data.get('factarea', '')}</td>
            	</tr>
            	<tr>
            		<td>质量检查机构：</td>
            		<td>{data.get('qccorpname', '')}</td>
            		<td><mark>验收</mark>日期：</td>
            		<td>{data.get('createdate', '')}</td>
            	</tr>
            	<tr>
            		<td>实际<mark>开工</mark>日期：</td>
            		<td>{data.get('bdate', '')}</td>
            		<td>实际<mark>竣工</mark>日期：</td>
            		<td>{data.get('edate', '')}</td>
            	</tr>
            </table>
                """
            return content

        if t == 10:
            content = f"""
                <table>
            	<tr>
            		<td>工程档号：</td>
            		<td colspan="3">{data.get('projectNo', '')}</td>
            	</tr>
            	<tr>
            		<td>工程名称：</td>
            		<td>{data.get('projectName', '')}</td>
            		<td>工程类别：</td>
            		<td>{data.get('projectType', '')}</td>
            	</tr>
            	<tr>
            		<td>工程地点：</td>
            		<td>{data.get('projectLocation', '')}</td>
            		<td>保管单位：</td>
            		<td>{data.get('settleCompany', '')}</td>
            	</tr>
            	<tr>
            		<td>建设单位：</td>
            		<td>{data.get('hostName', '')}</td>
            		<td>建设工程<mark>规划</mark><mark>许可</mark>证号：</td>
            		<td>{data.get('approveCert', '')}</td>
            	</tr>
            	<tr>
            		<td><mark>开工</mark>日期：</td>
            		<td>{data.get('projectStartDate', '')}</td>
            		<td><mark>竣工</mark>日期：</td>
            		<td>{data.get('projectEndDate', '')}</td>
            	</tr>
            </table>
                """
            return content


if __name__ == "__main__":
    CrawlerObject().start()
