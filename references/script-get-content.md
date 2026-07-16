# get_content 方法的写入规则

本文件只保留 `get_content` 规则和场景指引。完整真实脚本不要写入本文档，必须按本文档中标注的真实案例路径，直接读取对应的 `examples/*.py` 案例。



## HTML基础写法

- `get_content` 及其调用的全局辅助函数中，所有网络发包只能使用 `auto_request` 或从 `bbSpider` 导入的 `request`。
- 使用 `auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)` 请求详情页。
- 使用 `BeautifulSoup(resp.text, "html.parser")` 解析详情页。
- 使用 `content = soup.select_one(...)` 定位正文元素。
- 返回前使用 `handle_str.completion_url(str(content), params['url'])`。
- 返回字典使用 `params['title']`、`params['pubTime']`、`params['url']` 和处理后的 `content`。

真实案例：

- 常规 HTML 详情页解析正文：见 `examples/佳木斯大学附属第二医院(1)_招标(1)_1.py`。

## HTML特殊情况1：详情页补齐 pubTime

- 如果 `get_list` 中 `pubTime` 为 `None`，必须在 `get_content` 中补齐。
- 判断方式固定使用 `if params['pubTime'] is None:`。
- 如果详情页发布时间文本包含其他内容，必须使用 `handle_str.extract_and_validate_dates()` 提取日期。

真实案例：

- 列表页 `pubTime: None`，详情页补齐发布时间：见 `examples/山西省石楼县人民法院(1)_招标(1)_1.py`。

## HTML特殊情况2：get_list 已经提取 content

- 如果 `get_list` 已经提取正文内容，并且返回字典已包含 `url`、`title`、`pubTime`、`content`，则 `get_content` 不再发起请求，可以直接返回 `params`。
- 固定写法：

```python
if params.get('content'):
    return params
```

真实案例：

- JSON 列表接口已返回正文内容，`get_content` 直接 `return params`：见 `examples/湖北三峡职业技术学院附属医院(1)_招标(1)_1.py`。

## HTML特殊情况3：详情页补齐 title

- 如果 `get_list` 中 `title` 为 `None`，必须在 `get_content` 中补齐。
- 判断方式固定使用 `if params['title'] is None:`。
- 补齐后仍然返回 `params['title']`。

真实案例：

- 多栏目列表中某个分支返回 `title: None`，详情页补齐标题：见 `examples/湖州市医疗保障局(1)_招标(1)_1.py`。

## HTML特殊情况4：额外附件按抽样结果生成

- 分析阶段必须按用户指定的采集页数执行附件抽样：只采集 `1` 页时，仅在第一页的同源列表项中随机抽取 `3` 条详情页；采集多页时，必须在每个指定页分别随机抽取 `3` 条同源详情页。任一页不足 `3` 条同源列表项时，必须检查该页全部实际可用条目。
- 只有抽样发现 `.pdf`、`.doc`、`.docx`、`.xls`、`.xlsx` 额外附件时，才在 `get_content` 中生成对应附件提取和追加代码。
- 附件提取必须使用抽样确认的具体 DOM 或 JSON 字段，禁止在未发现附件时生成遍历所有 `<a>` 的猜测性代码。

## HTML特殊情况5：正文为内嵌 PDF

- 如果正文通过 `iframe`、`object`、`embed` 展示 PDF，必须从 `src` 或 `data` 等实际属性提取真实 PDF URL，使用 `soup.new_tag('a', href=..., string='内容附件')` 转换为链接并追加到 `content`。
- 原 `iframe`、`object`、`embed` 标签如果不再有保留价值，可以在追加 `<a>` 后使用 `decompose()` 移除。
- 真实案例写法参考：`examples/合肥综合性国家科学中心大健康研究院(1)_招标(1)_1.py`。

## HTML特殊情况6：PDF URL 存在于 JavaScript

- 必须先使用 BeautifulSoup 定位正文或相关 `script` 标签。只有脚本参数无法用 BeautifulSoup 直接提取时，才允许对该局部内容使用 `re`。
- 提取 PDF URL 后，使用 `soup.new_tag()` 创建带“内容附件”标识的 `<a>` 标签并追加到 `content`。
- 如果页面还存在独立附件区，必须同时追加该附件区，不得因已提取 PDF 而忽略其他附件。
- 真实案例写法参考：`examples/河南经贸职业学院(3)_招标(1)_1.py`。



## JSON特殊情况1：正文接口依赖列表页参数

- 列表页和详情页都是 JSON 接口时，`get_list` 可以把详情接口需要的 `id`、`articleId`、`projectId`、`noticeId`、`categoryId`、`detailUrl`、`detail_url` 等参数一并返回。
- `get_content` 必须直接从 `params` 中读取这些参数，用来拼接详情接口URL、查询参数、`data` 或 `json`。
- `params['url']` 始终表示文章详情页URL。
- 只有文章详情页URL本身就是 JSON 详情接口时，才直接使用 `params['url']` 请求正文。
- 如果实际请求正文的是另一个 JSON 详情接口，应新建局部变量 `url` 或使用 `params['detail_url']` 请求详情接口，最终返回结果中的 `url` 仍使用 `params['url']`。

真实案例：

- `get_list` 返回展示详情页 `url` 和 JSON 正文接口 `detail_url`，`get_content` 使用 `params['detail_url']` 请求正文：见 `examples/上海科技馆(1)_招标(1)_1.py`。

## JSON特殊情况2：以表单或载荷形式请求正文接口

- 如果详情接口需要 `data` 或 `json`，则在 `get_content` 中从 `params` 取列表页返回的字段组装请求参数。
- 需要发起业务请求时必须使用 `auto_request`；列表接口已提供完整正文时不得重复请求。
- 如果详情请求参数来自任务字典中的统一请求参数容器，该容器仍必须命名为 `data`；发送时再按真实请求映射为 GET `params`、POST `data` 或 POST `json`。
- `data`、`params` 和 `json` 只表示请求参数容器及其发送映射，不作为栏目分支判断依据。

## JSON特殊情况3：列表接口已包含正文 content

- 如果 `get_list` 已经返回 `content`，`get_content` 不需要再次请求详情页。
- `params` 必须已经包含 `url`、`title`、`pubTime`、`content`。
- 固定写法：

```python
if params.get('content'):
    return params
```

真实案例：

- JSON 列表接口直接返回 `content`：见 `examples/湖北三峡职业技术学院附属医院(1)_招标(1)_1.py`。
