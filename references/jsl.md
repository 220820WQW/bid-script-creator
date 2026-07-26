# 加速乐站点特殊处理

确认目标栏目命中加速乐特征时，完整遵守本文件。加速乐不再是硬性停止条件；只有浏览器 MCP 无法正常加载栏目页面时才停止。

## 识别特征

- 正常访问需要连续三次请求，前两次为 521，第三次为 200。
- 第一次响应返回 `__jsluid_s`，HTML 包含 `document.cookie=('_')+('_')+...` 或同类脚本，执行后生成 `__jsl_clearance_s`。
- 第二次携带两个 Cookie 仍返回 521，并通过混淆 JavaScript 生成新的 `__jsl_clearance_s`。
- 第三次携带更新后的 Cookie 返回 200。

## 分析流程

1. 使用本机可用的浏览器 MCP 访问目标网站栏目。
2. 页面持续空白、无法正常加载栏目内容时，停止生成脚本，并说明浏览器无法加载加速乐栏目页面。
3. 页面能够正常加载时，继续按照 `SKILL.md` 和 `site-analysis.md` 完成栏目、列表、详情及附件分析；不得因前两次请求返回 521 而停止。

## 生成规则

1. 增加以下按需导包

```python
import json
import re
import subprocess

from bbSpider.agent_pool import agent_pool
```

2. 在全局写入以下三个固定函数。
3. `solve_first_cookie()` 和 `solve_second_cookie()` 必须直接复用，禁止修改。
4. `get_cookies()` 只允许替换目标首页 URL，不得修改请求顺序、请求参数、Cookie 合并及有效性判断。
5. `subprocess` 调用 Node 只用于执行固定加速乐 challenge，是禁止外部命令和外部 JS 运行时规则的加速乐例外。

```python
def solve_first_cookie(challenge_html: str) -> str:
    match = re.search(r"document\.cookie=(.+?);location\.href", challenge_html)
    if not match:
        return ""
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
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8,"
            "application/signed-exchange;v=b3;q=0.7"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.google.com/",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "Sec-CH-UA": (
            '"Not;A=Brand";v="8", "Chromium";v="150", '
            '"Google Chrome";v="150"'
        ),
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
    }

    url = "当前目标站点首页或任意栏目页面的绝对 URL"
    first_response = request.get(
        url,
        headers=headers,
        timeout=30,
        proxy_safety="https",
        proxies=proxies,
    )
    cookies = first_response.cookies.get_dict()
    if not cookies:
        return None

    first_cookie = solve_first_cookie(first_response.text)
    k, v = first_cookie.split("=")
    cookies[k] = v

    second_response = request.get(
        url,
        headers=headers,
        timeout=30,
        proxy_safety="https",
        proxies=proxies,
    )
    second_cookie = solve_second_cookie(second_response.text)
    k, v = second_cookie.split("=")
    cookies[k] = v

    if len(cookies) < 2:
        return None

    return cookies
```

目标站点使用 HTTP 时，固定模板中的 `proxy_safety` 和方法调用处选取的代理键按真实协议使用 `http`；HTTPS 使用 `https`。除协议映射和 `url` 外，不修改固定流程。

## 核心方法调用

`get_list` 在列表请求前固定执行：

```python
for _ in range(8):
    proxies = agent_pool(params["url"])["https"]
    cookies = get_cookies(proxies=proxies)
    if cookies is None:
        continue
    break
else:
    return ret_list

cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
headers = HEADERS.copy()
headers["Cookie"] = cookie_str
```

随后使用局部 `headers` 和同一个 `proxies` 发起列表业务请求。

`get_content` 使用相同的 8 次代理与 Cookie 获取流程，但循环失败时返回 `None`。随后使用局部 `headers` 和同一个 `proxies` 发起详情业务请求。

`agent_pool(url)` 返回代理字典，必须根据目标 URL 的实际协议选择对应键，禁止固定选择错误协议。

## 案例与交付

1. 真实案例统一从 `examples/jsl/` 检索，只读取与目标协议、请求方式和数据结构最接近的少量案例。
2. 最终仍只交付用户指定的 Python 脚本，不创建额外文件。
3. 交付时提示用户运行环境必须能够调用 Node.js；不得运行完整采集脚本验证 challenge。

