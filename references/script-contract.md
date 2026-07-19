# SBKJ 采集脚本模板辅助说明

本文件只说明模板的固定结构和常用函数含义，不是核心生成规则。核心规则以 `SKILL.md` 为准；

`init_func`、`get_list`、`get_content` 的具体写法以对应 references 文档为准。

## 基本模板结构

每个生成脚本都遵循以下代码结构：

```python
# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from bbSpider import Spider, request, handle_str


# region fixed methods
# auto_request(...)
# is_same_origin_url(...)
# endregion


HEADERS = {}
COOKIES = {}


class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        ...

    def get_list(self, params: dict):
        ...

    def get_content(self, params: dict):
        ...


if __name__ == "__main__":
    CrawlerObject().start()
```



### 全局作用域说明

全局作用域约束以 `SKILL.md` 为准。本文件只保留模板中固定存在的全局结构：固定导包、固定公用方法、`HEADERS = {}`、`COOKIES = {}`、`CrawlerObject` 类和入口代码。站点确需加密、解密、签名或特殊数据还原时，只允许增加一个供主流程调用的语义化能力入口，以及该入口实际依赖的最少固定常量和内部辅助函数。未从该入口调用链到达的逆向、调试或通用库代码不得写入脚本。



## 固定代码区域

### 固定基础导包

下列为所有脚本必须保留的基础导包。只有站点的加解密、签名、编码或特殊解析实现确有需要时，才允许在此基础上增加最少量的标准库或已安装依赖导包；禁止删除基础导包或增加未使用的导包：

```python
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from bbSpider import Spider, request, handle_str
```



### 固定公用方法

正常生成脚本时，不要修改这段区域代码，直接复用：

```python
# region fixed methods
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
```



### 固定类成员变量

正常生成脚本时，不要修改这段区域代码，直接复用：

```python
start_urls = []
data_category = 0
collect_thread_number = 2
is_upload_data = 0
filter_type = "url"
```



### 固定类名和方法名

正常生成脚本时，类方法名固定，禁止修改。

```python
class CrawlerObject(Spider):
    ...

    @classmethod
    def init_func(cls):
        ...

    def get_list(self, params: dict):
        ...

    def get_content(self, params: dict):
        ...
```



### 固定全局入口

正常生成脚本时，不要修改这段区域代码，直接复用：

```python
if __name__ == "__main__":
    CrawlerObject().start()
```



## 常用函数说明

### auto_request

自动区分 GET / POST；

`auto_request` 是采集脚本的首选发包入口。`get_list`、`get_content` 以及全局辅助函数中的 Cookie/Token 初始化、风控握手、请求头生成等前置请求，都必须使用 `auto_request` 或从 `bbSpider` 导入的 `request`。禁止使用任何其他 HTTP 客户端或外部命令发包。

```python
def auto_request(url, params=None, data=None, json=None, proxy_safety=None, **kwargs):
    proxy_safety = urlparse(url).scheme if proxy_safety is None else proxy_safety

    if data is not None or json is not None:
        resp = request.post(url, params=params, data=data, json=json, proxy_safety=proxy_safety, **kwargs)
    else:
        resp = request.get(url, params=params, proxy_safety=proxy_safety, **kwargs)

    resp.encoding = resp.apparent_encoding
    return resp
```

- param url：请求地址
- param params：URL 查询参数
- param data：表单 data
- param json：JSON 请求体
- param proxy_safety：代理类型: http / https
- param kwargs：自动接收 headers / cookies / timeout / allow_redirects / verify / proxies 等



### is_same_origin_url

判断两个URL是否同源（仅对比域名，忽略www和大小写）。

```python
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
```



### completion_url

`bbSpider.handle_str.handle_str.completion_url()` ：将html页面的a标签中相对路径链接补全为绝对路径

```python
def completion_url(text, url):
    """
    补全HTML中的相对链接和绝对链接，支持src和href
    """
    hrefs = re.findall(r'(src|href)=(["|\'])(.*?)(["|\'])', text)
    for href in hrefs:
        if _is_list_item_prfix(['', '#', 'javascript:;', 'javascript:void(0);'], href[2]):
            continue
        full_href = urljoin(url, href[2])
        text = text.replace(f"{href[0]}={href[1]}{href[2]}{href[3]}", f"{href[0]}={href[1]}{full_href}{href[3]}")

    return text
```

- params text：只能是`content`字符串。
- params url：【硬性规则】必须是同源的URL绝对路径。



### time_stamp

`bbSpider.handle_str.handle_str.time_stamp()` ：13位时间戳转成 `%Y-%m-%d %H:%M:%S` 格式的字符串。

```python
def time_stamp(time_num):
    """
    13位时间戳
    时间戳转换
    """
    time_array = time.localtime(float(time_num/1000))
    other_style_time = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
    return other_style_time
```

示例：

```python
from bbSpider.handle_str import time_stamp

t = time_stamp(1766802770000)
print(t)  # 2025-12-27 10:32:50
```



### extract_and_validate_dates

`bbSpider.handle_str.handle_str.extract_and_validate_dates()`：用于从输入的字符串或 HTML 内容中提取并验证日期。

> 本 Skill 使用 `extract_and_validate_dates()` 时，该函数只负责提取以下三类仅含年月日的日期格式。月、日允许一位或两位数字：
>
> - `2026-07-15`、`2026-7-15`、`2026-7-1`、`2026-07-1`
> - `2026年07月15日`、`2026年7月15日`、`2026年7月1日`、`2026年07月1日`
> - `2026.07.15`、`2026.07.1`、`2026.7.15`、`2026.7.1`
>
> 该函数不负责保留时、分、秒，也不用于提取中文大写日期、斜杠日期、纯数字日期、英文日期或其他未列出的格式。即使下方展示的框架函数源码还具备识别其他格式的能力，生成采集脚本时也只使用上述三类提取结果。

该函数的提取能力不等同于 `pubTime` 的全部允许格式。`pubTime` 还可以直接保留不含额外字符的 `YYYY-MM-DD HH:MM` 或 `YYYY-MM-DD HH:MM:SS` 日期时间字符串；只有原始发布时间包含前缀、栏目名、来源等额外字符时，才使用本函数提取其中的纯日期。

```python
def extract_and_validate_dates(text):
    """
    从给定的HTML/文本输入中提取并验证日期字符串。
    该函数解析输入文本（可能包含HTML），提取所有纯文本内容，
    并搜索包含标准数字格式和中文大写数字的日期模式。
    支持的日期格式包括：
        - 年-月-日 或 年-月-日（例如：“2024-6-5”，“2024-06-05”）
        - YYYY年M月D日（例如，“2024年6月5日”）
        - 年.月.日（例如，“2024.6.5”）
        - 中文大写数字（例如，“二〇二五年十一月十九日”）
    发现的日期经过验证后以列表形式返回。中文大写数字日期会被转换
    在验证前转换为标准格式。
    Args:
        text (str): 用于提取日期的输入字符串或HTML内容。
    Returns:
        list: 返回匹配到的日期列表数据
    """
    
    if not isinstance(text, str):
        raise TypeError("参数必须为 `str` 类型")
    soup = BeautifulSoup(text, 'html.parser')
    
    # 提取所有文本内容
    text = soup.get_text()

    # 修正中文大写数字日期的模式
    date_patterns = {
        r'\d{4}-\d{1,2}-\d{1,2}': '%Y-%m-%d',      # YYYY-M-D 或 YYYY-MM-DD
        r'\d{4}年\d{1,2}月\d{1,2}日': '%Y年%m月%d日',  # YYYY年M月D日
        r'\d{4}\.\d{1,2}\.\d{1,2}': '%Y.%m.%d',     # YYYY.M.D
        r'二[O〇零一二三四五六七八九]{3}年[一二三四五六七八九十]{1,2}月[一二三四五六七八九十]{1,3}日': None  # 中文大写数字，如"二〇二五年十一月十九日"
    }
    
    valid_dates = []
    
    for pattern, date_format in date_patterns.items():
        matches = re.findall(pattern, text)
        for date_str in matches:
            try:
                if '二' in date_str and '年' in date_str and '月' in date_str and '日' in date_str:  # 中文大写数字日期
                    # 转换中文大写数字日期
                    converted_date = convert_chinese_date(date_str)
                    if converted_date:
                        # 验证转换后的日期
                        data = datetime.datetime.strptime(converted_date, '%Y-%m-%d').strftime("%Y-%m-%d")
                        valid_dates.append(data)
                else:
                    # 常规日期格式
                    datetime.datetime.strptime(date_str, date_format)
                    valid_dates.append(date_str)
            except ValueError:
                continue
    
    return valid_dates
```

示例：

```python
from bbSpider.handle_str import extract_and_validate_dates

text = """
正文内容
2026-07-02
"""

t = extract_and_validate_dates(text)
print(t)  # ['2026-07-02']
```



### replace_escape

`bbSpider.handle_str.handle_str.replace_escape()` ：替换字符串中的转义字符。

```python
def replace_escape(text):
    """
    替换一些转义符
    """
    re_cover = re.compile(r'[\n|\t|\r]', re.M)
    text = re.sub(re_cover, '', text)
    return text
```

