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



## 最简优先与修改纪律

1. 所有 agent 必须用最少的代码完成当前采集任务。只保留真实流程不可缺少的请求、解析、字段处理和契约代码；禁止增加未使用的功能、配置、兼容分支、备用选择器、推测性兜底或“以后可能使用”的参数。
2. 优先直接表达：简单表达式、赋值和调用能清楚写成一行时不要无意义拆行；同一值能复用时不要重复计算或构造；只调用一次且无需复用的简单逻辑不要额外封装。语句过长或嵌套难读时，最多增加必要的语义中间变量。
3. 删除重复逻辑、无意义中间层、未使用导包和非必要注释。同类逻辑放在一起，不同逻辑组适当留空；禁止用分号或单行控制流刻意压缩代码。
4. 只处理真实响应中已观察到的失败、契约明确要求的检查，以及会直接破坏正常流程的必要失败。每段站点相关代码都必须能追溯到用户需求、已验证响应、Skill 规则、bbSpider 契约或必要特殊流程，否则不得保留。
5. 瑞数、加速乐、阿里 `acw_sc__v2` 等特殊案例 reference 明确标记的固定代码不参与精简，必须完整保留其规定结构；不得因存在重复或可封装部分而擅自删改。
6. 修改已有脚本时只改完成当前任务必需的行，不顺便重构、格式化、修复或清理无关代码；只清理由本次修改直接产生的遗留内容。
7. 不确定的事实或存在会改变实现的多种解释时，必须先向用户说明并询问；禁止自行猜测、选择一种解释或添加兜底分支掩盖不确定性。



## 固定代码区域

正常生成脚本时，必须直接复用本节明确列出的固定代码、名称和结构，禁止修改这些固定区域。

允许根据目标站点的真实情况填写或实现 `HEADERS`、`COOKIES`、三个核心方法，以及确有必要的最少量站点常量、能力入口和辅助函数；这些可变内容不属于禁止修改的固定区域。



1. 固定基础导包

```python
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bbSpider import Spider, request, handle_str
```

- 上述为所有脚本必须保留的基础导包。
- 禁止删除基础导包或增加未使用的导包
- 只有站点的加解密、签名、编码或特殊解析实现确有需要时，才允许在此基础上增加最少量的标准库或已安装依赖导包。



2. 固定公用方法

```python
# region fixed methods
def auto_request(
    url, params=None, data=None, json=None, proxy_safety=None, **kwargs
):
    if proxy_safety is None:
        proxy_safety = urlparse(url).scheme

    if data is not None or json is not None:
        resp = request.post(
            url,
            params=params,
            data=data,
            json=json,
            proxy_safety=proxy_safety,
            **kwargs,
        )
    else:
        resp = request.get(
            url,
            params=params,
            proxy_safety=proxy_safety,
            **kwargs,
        )

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

上述固定公用方法的前后注释也要加上。



3. 固定类名、方法名、类成员变量、全局入口

上述“基本模板结构”中的 `CrawlerObject` 类名（包括继承的类名）、以下类成员变量、方法名（包括类方法名和实例方法名），以及底部的全局入口都必须直接复用，禁止修改：

```python
start_urls = []
data_category = 0
collect_thread_number = 2
is_upload_data = 0
filter_type = "url"
```

