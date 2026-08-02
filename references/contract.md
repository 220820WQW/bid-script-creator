# 采集脚本模板与框架契约

本文件定义采集脚本的固定模板、固定公共函数源码和框架契约。

目标网站分析规则以 `SKILL.md` 为准；`init_func`、`get_list`、`get_content` 的具体实现规则以对应 reference 为准。

## 基本模板结构

每个生成脚本框架都遵循以下代码结构：

```python
# -*- coding: UTF-8 -*-
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bbSpider import Spider, request, handle_str


# region fixed public func
# def auto_request(...)
# def is_same_origin_url(...)
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



## 生成代码质量约束

固定公共方法及特殊 reference 明确规定的固定代码不受精简和排版约束，必须完整保留其规定结构。

1. 只保留完成真实采集流程不可缺少的请求、解析、字段处理和契约代码；禁止增加未使用的功能、配置、兼容分支、备用选择器、推测性兜底或预留参数。
2. 优先直接表达并复用已有值，禁止重复计算、重复构造、无意义中间层和只使用一次的简单封装；仅在语句过长、嵌套难读或语义确有需要时增加中间变量。
3. 代码必须按语义分组。请求准备、网络请求与状态检查、响应解析、数据遍历、字段处理、附件处理和结果返回等相对独立的逻辑组之间使用一个空行；同一逻辑组内紧密相关的语句保持相邻。
4. 空行和换行只用于表达代码结构：禁止机械地在每条语句之间插入空行、连续保留三个及以上空行，也禁止使用分号、单行控制流或把多个独立操作写在同一行来压缩代码。
5. “最少代码”是减少无用逻辑和重复实现，不是减少代码行数；不得因此删除必要空行、压缩排版或牺牲可读性。
6. 修改已有脚本时只改完成当前任务必需的代码，禁止顺便重构、格式化、修复或清理无关内容；只清理由本次修改直接产生的遗留代码。



## 固定代码区域

正常生成脚本时，直接复用本节明确列出的固定代码、名称和结构，禁止修改这些固定区域。

允许根据目标站点的真实情况填写 `HEADERS`、`COOKIES`、三个核心方法，以及确有必要的最少量站点常量、能力入口和辅助函数；这些可变内容不属于禁止修改的固定区域。



### 固定基础导包

```python
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bbSpider import Spider, request, handle_str
```

- 上述为所有脚本必须保留的基础导包。
- 禁止删除基础导包或增加未使用的导包
- 只有站点的加解密、签名、编码或特殊解析实现确有需要时，才允许在此基础上增加最少量的标准库或已安装依赖导包。



### 固定公共方法

```python
# region fixed public func
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

- 整段代码直接复用（包括注释），禁止修改。



### 固定类名、方法名、类成员变量、全局入口

上述“基本模板结构”中的 `CrawlerObject` 类名（包括继承的类名）、以下类成员变量、方法名（包括类方法名和实例方法名），以及底部的全局入口都必须直接复用，禁止修改：

```python
start_urls = []
data_category = 0
collect_thread_number = 2
is_upload_data = 0
filter_type = "url"
```

