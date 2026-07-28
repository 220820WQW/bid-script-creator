# bbSpider 常用函数说明

本文件只说明固定公共函数和 bbSpider 辅助函数的函数功能和调用方式。

## 函数索引

- `auto_request()`：统一发送 GET 或 POST 请求。
- `is_same_origin_url()`：校验两个 URL 是否同源。
- `completion_url()`：补全正文中的相对链接。
- `time_stamp()`：转换毫秒级时间戳。
- `extract_and_validate_dates()`：从文本或 HTML 中提取并验证日期。
- `replace_escape()`：移除字符串中的换行、制表和回车字符。
- `acquire_subjoin_path()`：定位 `SubsidiaryDir` 中的本地附加文件。
- `agent_pool()`：从 bbSpider 获取代理。

### auto_request

自动区分 GET 和 POST，是采集脚本的首选发包入口。固定源码以 `contract.md` 的“固定代码区域”为准。

- `url`：请求地址。
- `params`：URL 查询参数。
- `data`：POST 表单。
- `json`：POST JSON 请求体。
- `proxy_safety`：代理类型，使用 `http` 或 `https`。
- `**kwargs`：传递 `headers`、`cookies`、`timeout`、`allow_redirects`、`verify`、`proxies` 等参数。
- 返回值：响应对象。

`get_list`、`get_content` 及全局辅助函数中的 Cookie/Token 初始化、风控握手和请求头生成等前置请求，都必须使用 `auto_request()` 或从 bbSpider 导入的 `request`。

### is_same_origin_url

判断两个 URL 是否同源，仅对比域名并忽略 `www` 和大小写，不比较协议、端口、路径或查询参数。调用时应优先复用当前作用域已有的目标网站同域 URL；只有没有可用的现有 URL 时才新增比较基准。固定源码以 `contract.md` 的“固定代码区域”为准，不得在此重新实现。

- `url_a`、`url_b`：需要比较的两个绝对 URL。
- 返回值：同源时为 `True`，否则为 `False`。

### completion_url

`handle_str.completion_url(text, url)` 用于将正文 HTML 中 `src` 和 `href` 的相对路径补全为绝对路径。

- `text`：字符串形式的 `content`。
- `url`：当前详情页的绝对 URL，作为链接补全基准。
- 返回值：完成链接补全后的 HTML 字符串。

```python
content = handle_str.completion_url(str(content), params["url"])
```

### time_stamp

`handle_str.time_stamp(time_num)` 将 13 位毫秒级时间戳转换为 `%Y-%m-%d %H:%M:%S` 格式字符串。

- `time_num`：毫秒时间戳，int类型；秒级时间戳必须先乘以1000。
- 返回pubTime可以直接使用的日期字符串。

```python
pubTime = handle_str.time_stamp(int(pub_time))  # 2026-07-26 06:30:10
```

### extract_and_validate_dates

`handle_str.extract_and_validate_dates(text)`：从字符串或 HTML 中提取仅含年月日的日期，返回匹配到的日期列表。

- `text`：包含年月日的日期字符串。
- 返回日期列表，例如：`['2026-07-26']`

支持的来源格式包括：

- `YYYY-M-D`、`YYYY-MM-DD`、`YYYY年M月D日`、`YYYY.M.D`
- 中文大写数字日期，例如：`二〇二六年七月一日`

该函数不提取时分秒。发布时间文本包含“发布时间”、栏目、来源等额外字符时，用它提取纯日期。

```python
pub_time = handle_str.extract_and_validate_dates(pub_time_text)[0]
```

### replace_escape

`handle_str.replace_escape(text)` 移除字符串中的 `\r`、`\t`、`\n`。

```python
title = handle_str.replace_escape(title).strip()
```

### acquire_subjoin_path

`acquire_subjoin_path(file_name)`：返回当前脚本 `SubsidiaryDir` 目录中指定本地附加文件的绝对路径。

只在需要读取本地附加文件时使用，例如：调用 Node 执行本地 JS。

```python
from bbSpider.utils import acquire_subjoin_path

js_path = acquire_subjoin_path("compute_cookie.js")
```

### agent_pool

`agent_pool(page_url)`：从 bbSpider 获取代理字典。

```python
from bbSpider.agent_pool import agent_pool

proxies = agent_pool(url)["https"]
```

- `page_url`：以 `http://` 或 `https://` 开头的绝对 URL。
- 返回代理字典，例如：`{'http': 'URL', 'https': 'URL'}`。
