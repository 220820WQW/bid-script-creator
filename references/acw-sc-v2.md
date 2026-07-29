# 阿里 acw_sc__v2 特殊处理

确认目标栏目命中阿里 `acw_sc__v2` challenge 时，完整遵守本文件。只有浏览器 MCP 无法正常加载栏目页面时才停止。

## 特征识别

不得只因页面出现 `renderData`、`aliyunwaf` 或某个 Cookie 就单独判定。必须结合首次响应和 HTML challenge 的多项特征确认。

### 首次响应

- 响应状态码通常为 200，而不是错误状态码。
- 响应 Cookie 中存在 `acw_tc`。
- 返回内容不是正常业务列表或详情，而是专门生成 `acw_sc__v2` 的 challenge HTML。

### HTML challenge

以下特征来自真实首次响应样本，随机后缀和具体值可能变化，应按结构识别：

1. 文档开头或 `doctype` 之前存在隐藏的 `textarea#renderData`，内容是 JSON；`l1` 字段包含类似 `var arg1='...';` 的动态 `arg1`。
2. 第一段脚本读取并解析 `renderData`，截取 `arg1`，定义 Cookie 写入和刷新逻辑，并显式出现 `setCookie("acw_sc__v2", ...)` 或等价的 `acw_sc__v2` 写入代码。
3. 另一段 `script` 的 `name` 以 `aliyunwaf_` 开头，内容是很长的自执行混淆函数；具体函数名、变量名和随机后缀不可作为固定特征。
4. 页面通常还存在 `meta[name="aliyun_waf_aa"]`、`meta[name="aliyun_waf_bb"]`，以及 `name` 以 `aliyunwaf_` 开头的第二个隐藏 `textarea`，其中包含较长 challenge 数据。
5. 执行首次 HTML 中的 challenge 后得到 `acw_sc__v2`；携带首次 `acw_tc` 和计算出的 `acw_sc__v2` 再次请求，响应状态码为 200 并返回正常业务内容。

确认时至少同时满足：首次响应具有 `acw_tc`；HTML 中具有 `textarea#renderData` 的 `l1/arg1`；脚本明确写入 `acw_sc__v2`；存在长混淆的 `aliyunwaf_` 脚本。其余 `aliyun_waf_aa/bb` 和隐藏 challenge textarea 用作增强证据。

## 分析流程

1. 使用本机可用的浏览器 MCP 访问目标网站栏目。
2. 页面无法正常加载或持续超时时，停止生成脚本，并说明浏览器无法加载该 `acw_sc__v2` 栏目页面。
3. 页面正常加载时继续按照 `SKILL.md` 和 `site-analysis.md` 完成栏目、列表、详情及附件分析；不得因直接请求只返回 challenge HTML 而停止。

## 生成规则

1. 增加以下按需导包

```python
import json
import os
import subprocess
import sys
import tempfile

from bbSpider.agent_pool import agent_pool
from bbSpider.utils import acquire_subjoin_path
```

2. 在全局写入固定 `compute_cookie()` 和 `get_cookies()`。
3. `compute_cookie()` 必须直接复用，固定读取 `acquire_subjoin_path("compute_cookie.js")`，禁止修改文件名、临时文件流程、Node 调用、超时和清理逻辑。
4. `get_cookies()` 只允许替换能够触发同一 challenge 的首页、栏目页面或接口绝对 URL；优先使用页面 URL。函数内的网络请求必须固定使用从 `bbSpider` 导入的 `request`，禁止改为 `auto_request` 或调整发包方式，其余结构保持不变。
5. `subprocess` 调用 Node 只用于执行固定 `compute_cookie.js`，是禁止外部命令和外部 JS 运行时规则的本流程例外。

```python
def compute_cookie(html_text):
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    )
    try:
        tmp.write(html_text)
        tmp.close()
        result = subprocess.run(
            ["node", acquire_subjoin_path("compute_cookie.js"), tmp.name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        return result.stdout.strip()
    finally:
        os.unlink(tmp.name)


def get_cookies(proxies=None):
    headers = {
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8,"
            "application/signed-exchange;v=b3;q=0.7"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Referer": "https://www.qphospital.com/article/category/news",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/132.0.0.0 Safari/537.36"
        ),
    }

    url = "可触发 acw_sc__v2 的首页、栏目页面或接口绝对 URL"
    response = request.get(
        url,
        headers=headers,
        proxies=proxies,
        proxy_safety="https",
    )
    cookies = dict(response.cookies)
    if not cookies:
        return None

    if "renderData" in response.text and "acw_sc__v2" in response.text:
        acw_sc_v2 = compute_cookie(response.text)
        if not acw_sc_v2:
            print(
                json.dumps(
                    {"error": "计算 acw_sc__v2 失败"},
                    ensure_ascii=False,
                )
            )
            sys.exit(1)

        cookies["acw_sc__v2"] = acw_sc_v2
        return cookies
    else:
        return None
```

目标站点使用 HTTP 时，固定模板中的 `proxy_safety` 和方法调用处选取的代理键按真实协议使用 `http`；HTTPS 使用 `https`。除协议映射和触发 URL 外，不修改固定流程。

## 核心方法调用

`agent_pool(url)` 取得代理后，将所选代理传给 `get_cookies()`；Cookie 获取和后续业务请求必须使用同一个 `proxies`。ACW 流程取得 Cookie 后直接通过 `cookies=cookies` 传给业务请求，不转换成 Cookie 请求头。

`get_list` 在列表请求前固定执行：

```python
for _ in range(8):
    proxies = agent_pool(params["url"])["https"]
    cookies = get_cookies(proxies)
    if cookies:
        break
else:
    return ret_list
```

随后使用 `auto_request`、本次 `cookies` 和同一个 `proxies` 发起列表业务请求。

`get_content` 在详情请求前固定执行：

```python
for _ in range(8):
    proxies = agent_pool(params["url"])["https"]
    cookies = get_cookies(proxies)
    if cookies:
        break
else:
    return None
```

随后使用 `auto_request`、本次 `cookies` 和同一个 `proxies` 发起详情业务请求。上述示例使用 HTTPS；目标为 HTTP 时，两个方法都必须将代理键改为 `"http"`。

## 案例与交付

1. 参考真实案例统一从 `examples/acw_sc__v2/` 检索，只读取与目标协议、challenge 入口、请求方式和数据结构最接近的少量案例。
2. 最终只交付用户指定的 Python 脚本，不创建 `compute_cookie.js` 或其他额外文件。
3. 交付时明确提示用户：运行环境需要 Node.js，并需要在 `SubsidiaryDir` 中自行提供固定名称 `compute_cookie.js`。
