# 瑞数站点特殊处理

确认目标栏目命中瑞数特征时，完整遵守本文件。瑞数不再是硬性停止条件；只有浏览器 MCP 无法正常加载栏目页面时才停止。

## 识别特征

- 首次响应状态码为 202 并返回 Cookie。
- `head` 中存在 `content` 为较长字符串的 `meta` 标签，可能带 `id`。
- 页面脚本出现 `$_ts = windows['$_ts'];` 或同类 `$_ts` 代码，并加载内容固定的外链 JavaScript。
- 执行相关脚本后生成新 Cookie，携带首次 Cookie 和新 Cookie 的第二次请求返回 200。

## 分析流程

1. 使用本机可用的浏览器 MCP 访问目标网站栏目。
2. 页面持续空白、无法正常加载栏目内容时，立即停止生成脚本，并说明浏览器无法加载瑞数栏目页面。
3. 页面能够正常加载时，继续按照 `SKILL.md` 和 `site-analysis.md` 完成栏目、列表、详情及附件分析；不得因直接请求返回 202 而停止。

## 生成规则

1. 增加以下按需导包：

```python
import execjs
from bbSpider.utils import acquire_subjoin_path
```

2. 在全局写入固定 `get_cookies()`。函数结构保持不变，只允许替换本节后面列出的两个站点值。
3. `execjs` 和本地 JS 文件只用于瑞数 Cookie 计算，是网络请求约束中禁止外部 JS 运行时的唯一例外。

```python
def get_cookies():
    for _ in range(8):
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
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/132.0.0.0 Safari/537.36"
            ),
        }

        url = "当前目标站点首页或栏目页面的绝对 URL"
        response = request.get(url, headers=headers, verify=False)
        cookies = response.cookies.get_dict()

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.select_one("meta[id][content]").get("content")
        code = soup.select_one("script").text

        src = soup.select_one("head script[src]").get("src")
        domain_url = urljoin(url, src)
        resp = request.get(domain_url, headers=headers)
        if resp.status_code != 200:
            continue

        domain = resp.text

        path = acquire_subjoin_path("目标站点名称1.js")
        with open(path, "rt", encoding="utf-8") as file:
            js_code = file.read()

        output = execjs.compile(js_code).call(
            "general_cookie", content, code, domain
        )
        cookies.update(output)
        if len(cookies) < 2:
            continue

        return cookies
    else:
        return None
```

只允许替换：

1. `url`：当前目标站点首页或任意一个能够触发同一瑞数流程的栏目页面绝对 URL。
2. `acquire_subjoin_path()` 中的 JS 文件名：使用语义明确且与目标站点对应的文件名，例如 `目标站点名称1.js`。只写文件名，不检查文件是否存在，也不生成该 JS 文件。

禁止修改重试次数、请求顺序、选择器、`general_cookie` 函数名、Cookie 合并及有效性判断结构；目标站点已验证的瑞数结构与固定模板不一致时，先向用户说明，不得自行改造模板。

## 核心方法调用

`get_list` 在列表请求前固定写入：

```python
cookies = get_cookies()
if cookies is None:
    return ret_list
```

随后把 `cookies` 传给列表请求，不使用空的全局 `COOKIES`。

`get_content` 在详情请求前固定写入：

```python
cookies = get_cookies()
if cookies is None:
    return None
```

随后把 `cookies` 传给详情请求。列表或详情还有独立接口时，也必须按真实请求链使用本次取得的 Cookie。

## 案例与交付

1. 真实案例统一从 `examples/ruishu/` 检索，只读取与目标请求方式和数据结构最接近的少量案例。
2. 最终只交付用户指定的 Python 脚本，不创建外部 JS 文件。
3. 交付时明确提示用户：需要在 `SubsidiaryDir` 中自行创建脚本引用的 JS 文件。

