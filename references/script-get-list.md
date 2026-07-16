# get_list方法的写入规则

本文件只保留 `get_list` 规则和场景指引。完整真实脚本不要写入本文档，必须按本文档中标注的真实案例路径，直接读取对应的 `examples/*.py` 案例。

## 请求参数映射

- 【硬性规则】`get_list` 及其调用的全局辅助函数中，所有网络发包只能使用 `auto_request` 或从 `bbSpider` 导入的 `request`。
- 【硬性规则】`params` 形参中由 `payload_list` 传入的请求参数必须位于 `params['data']`。
- GET 查询参数：`auto_request(url=params['url'], params=params['data'], ...)`。
- POST 表单：`auto_request(url=params['url'], data=params['data'], ...)`。
- POST JSON 载荷：`auto_request(url=params['url'], json=params['data'], ...)`。
- 必须以网站真实请求方式选择上述映射，禁止仅根据容器名 `data` 判断请求方式。

## HTML基础写法

- 使用 `BeautifulSoup(resp.text, "html.parser")` 解析。
- 使用 `rows = soup.select(...)` 获取列表。
- 使用 `a_tag = row.select_one('a')` 获取链接元素。
- 对每个列表项，先使用 `urljoin('用户给出的目录网站URL', a_tag.get('href'))` 生成绝对详情 URL。
- 紧接着必须使用 `is_same_origin_url(url, '用户给出的目录网站URL')` 校验同源并过滤附件；不得使用可能不同源的接口 URL 作为比较基准。
- 非同源链接立即 `continue`；只有同源链接才继续提取标题、时间并执行 `ret_list.append()`。
- 使用 `get_text(strip=True)` 提取标题和发布时间。
- 每条 `ret_list.append()` 至少返回 `url`、`title`、`pubTime`。

真实案例：

- HTML 基础列表页，并从发布时间文本中提取日期：见 `examples/佳木斯大学附属第二医院(1)_招标(1)_1.py`。

## HTML特殊情况1：列表页没有发布时间

- 如果列表页没有提供发布日期，或发布日期不完整，则将 `pubTime` 设置为 `None`。
- `get_content` 中必须使用 `if params['pubTime'] is None:` 补齐。
- 不要用空字符串、`''`、`'None'` 作为需要补齐的标记。

真实案例：

- `get_list` 返回 `pubTime: None`，详情页补齐发布时间：见 `examples/山西省石楼县人民法院(1)_招标(1)_1.py`。

## HTML特殊情况2：发布时间包含其他文本

- 如果 `pubTime` 中包含 `发布时间：`、栏目名、来源等其他文本，必须使用 `handle_str.extract_and_validate_dates()` 提取日期。
- 如果页面已经直接给出干净日期，不要额外处理。

真实案例：

- 列表页 `pubTime` 使用 `handle_str.extract_and_validate_dates(pubTime)[0]` 清洗：见 `examples/佳木斯大学附属第二医院(1)_招标(1)_1.py`。

## HTML特殊情况3：发布时间分散在多个元素

- 如果日期分散在多个元素中，例如年/月在一个元素、日在另一个元素，可以分别提取后拼接。
- 拼接后必须形成可识别的完整日期，例如 `YYYY-mm-dd`。
- 这类场景没有固定模板，必须根据页面实际元素位置编写。

真实案例：提取发表日期见：`examples/泉州医学高等专科学校(2)_招标(1)_1.py`

## HTML特殊情况4：多个栏目列表结构不一致

- 如果多个栏目共用 `get_list`，但列表页 HTML 结构、详情URL拼接方式、标题位置、发布时间位置等不一致，可以在 `payload_list` 中为每个栏目增加顶层 `t` 字段区分类型。
- 栏目类型区分字段必须只能使用顶层 `t`，禁止使用顶层 `type`、`category`、`kind`、`column` 等其他字段名。
- 顶层 `t` 字段必须在 `init_func` 中随 `start_urls` 一起传入，例如：`{'url': p['url'], 't': p['t']}`。
- `get_list` 中允许使用 `if params['t'] == 1:`、`if params['t'] == 2:` 这类分支分别解析。
- 如果多个栏目的提取规则一致，禁止为了栏目名称不同而添加分支，必须使用统一解析逻辑。
- 每个分支内部仍然必须保持简短清晰，并且每条 `ret_list.append()` 至少返回 `url`、`title`、`pubTime`。
- 无论哪个分支，`url` 都必须在 `get_list` 中生成为绝对 URL，并且必须使用 `is_same_origin_url()` 校验其与用户给出的目录网站 URL 同源。

真实案例：

- 多栏目接口返回 HTML，按顶层 `t` 分支解析不同列表结构，并在其中一个分支返回 `title: None`：见 `examples/湖州市医疗保障局(1)_招标(1)_1.py`。





## JSON特殊情况1：url 从接口中提取

1. 只能提取到部分 URL 时，必须使用 `urljoin()` 和用户给出的目录网站 URL 拼接为绝对 URL。
2. 提取到完整 URL 或完成相对 URL 拼接后，必须使用 `is_same_origin_url(详情URL, 用户给出的目录网站URL)` 校验同源。
3. 接口 URL 只用于请求数据，不得代替用户给出的目录网站 URL 作为同源判断基准。

如果详情页正文请求依赖接口返回的 `id`、`articleId`、`projectId`、`noticeId`、`categoryId`、`detailUrl` 等参数，必须一并返回给 `get_content` 使用。

真实案例：

- JSON 列表返回 `id`，`get_list` 生成展示详情页 `url`，同时返回 `detail_url` 给 `get_content` 请求正文接口：见 `examples/上海科技馆(1)_招标(1)_1.py`。

## JSON特殊情况2：接口返回时间戳

- 接口返回的日期是毫秒级时间戳时，使用 `handle_str.time_stamp(int(pubTime))` 转成 `YYYY-mm-dd`。
- 接口返回的日期是秒级时间戳时，必须先乘以 1000，再使用 `handle_str.time_stamp(int(pubTime) * 1000)`。
- 不要添加额外异常判断，按接口实际返回格式直接转换。
- 真实案例：接口返回时间戳见：`examples/烟台市博物馆(1)_招标(1)_1.py`

## JSON特殊情况3：多个栏目接口结构不一致

- 如果多个栏目共用 `get_list`，但接口返回字段、详情URL拼接方式、标题字段、发布时间字段等不一致，可以在 `payload_list` 中为每个栏目增加顶层 `t` 字段区分类型。
- 栏目类型区分字段必须只能使用顶层 `t`，禁止使用顶层 `type`、`category`、`kind`、`column` 等其他字段名。
- `t` 字段必须在 `init_func` 中随 `start_urls` 一起传入，例如：`{'url': p['url'], 'data': p['data'].copy(), 't': p['t']}`。
- `data` 内部字段始终是接口请求参数，不能作为脚本栏目分支判断依据；如果接口本身需要 `type`、`category` 等请求参数，只能放在 `data` 内部。
- `get_list` 中允许使用 `if params['t'] == 1:`、`if params['t'] == 2:` 这类分支分别解析。
- 如果多个栏目的接口字段结构一致，禁止为了栏目名称不同而添加分支，必须使用统一解析逻辑。
- 每个分支内部仍然必须保持简短清晰，并且每条 `ret_list.append()` 至少返回 `url`、`title`、`pubTime`。
- 无论哪个分支，`url` 都必须在 `get_list` 中生成。
- GET 接口分页也可以使用顶层 `t`，随 `start_urls` 一起传入，例如：`{'url': p['url'].format(index), 't': p['t']}`。

真实案例：

- 多栏目接口返回 HTML 并使用顶层 `t` 分支：见 `examples/湖州市医疗保障局(1)_招标(1)_1.py`。

## JSON特殊情况4：列表接口已包含正文 content

- 如果接口列表中已经包含正文内容，可以在 `get_list` 返回中带上 `content`。
- `content` 返回前应按实际情况使用 `handle_str.completion_url(str(content), params['url'])` 补全正文中的相对链接。
- 后续 `get_content` 中可使用 `if params.get('content'):` 判断，命中后可直接 `return params`，也可显式构造结果；只要返回字典包含 `title`、`pubTime`、`url`、`content` 四个必需字段即可。
- 这种情况下 `get_list` 返回字典必须已经包含 `url`、`title`、`pubTime`、`content`。

真实案例：

- JSON 列表接口直接返回 `content` 的数据来源可参考 `examples/湖北三峡职业技术学院附属医院(1)_招标(1)_1.py`，但 `get_content` 的返回方式必须以 `references/script-get-content.md` 为准。
