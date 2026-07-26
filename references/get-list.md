# get_list 方法约束

真实案例统一按 `SKILL.md` 的“真实案例检索目录路由表”查找，本文件只维护 `get_list` 的完整方法约束，不维护案例路径。

## 方法接口与返回值

- 形参名固定为 `params`，禁止修改、增加或删除形参。
- 返回值必须是 `list`，并固定使用 `ret_list` 变量名。
- HTTP 状态码为 4xx 或 5xx 时返回空列表 `ret_list`。
- 每个返回字典至少包含 `url`、`title`、`pubTime`，字段名不可更改。
- 禁止添加无依据的异常捕获，按已经确认的正常响应结构编写简洁代码。

## 请求参数映射

- 【硬性规则】`get_list` 及其调用的全局辅助函数中，所有网络发包只能使用 `auto_request` 或从 `bbSpider` 导入的 `request`。
- 【硬性规则】`params` 形参中由 `payload_list` 传入的请求参数必须位于 `params['data']`。
- GET 查询参数：`auto_request(url=params['url'], params=params['data'], ...)`。
- POST 表单：`auto_request(url=params['url'], data=params['data'], ...)`。
- POST JSON 载荷：`auto_request(url=params['url'], json=params['data'], ...)`。
- 必须以网站真实请求方式选择上述映射，禁止仅根据容器名 `data` 判断请求方式。
- 确认瑞数时，列表请求前必须按 `references/ruishu.md` 调用 `get_cookies()`；返回 `None` 时返回空的 `ret_list`，成功时把本次 Cookie 传给列表请求。
- 确认加速乐时，必须按 `references/jsl.md` 使用 `agent_pool` 和固定 challenge 流程取得代理与 Cookie；8 次失败后返回空的 `ret_list`，成功后使用局部 Cookie 请求头和同一个代理发送列表请求。
- 确认阿里 `acw_sc__v2` 时，必须按 `references/acw-sc-v2.md` 使用 `agent_pool` 和固定 Cookie 流程；8 次失败后返回空的 `ret_list`，成功后通过 `cookies=cookies` 和同一个代理发送列表请求。

## URL 构造与变量复用

1. 构造详情 URL 和执行同源校验时，优先复用当前作用域中已经存在且语义正确的 URL 变量，避免重复书写较长的 URL 字面量。
2. `params['url']` 确实是列表页 URL，并且可以作为相对详情链接的补全基准时，优先写成：

```python
url = urljoin(params['url'], a_tag.get('href'))
if not is_same_origin_url(url, params['url']):
    continue
```

3. `params['url']` 是列表接口 URL、与用户给出的目录网站 URL 不同，或不能作为正确补全基准时，不得为了简写而错误复用。此时把已经确认的目录网站 URL 保存为语义明确的局部变量，例如 `site_url` 或 `list_url`，并在 `urljoin()` 和 `is_same_origin_url()` 中复用；禁止因此新增全局 URL 常量。
4. URL 的固定结构已经明确，只需插入 ID、页码、栏目值或其他变量即可得到完整 URL 时，优先直接使用 f-string：

```python
url = f"https://example.com/detail?id={article_id}&type={notice_type}"
```

5. 能用一个清晰 f-string 得到完整 URL 时，禁止使用字符串相加、多段括号字符串、`format()`，也不要先构造相对字符串再调用 `urljoin()`。
6. 只有真实字段可能返回相对路径、根路径或完整 URL，需要遵循 URL 解析与补全语义时，才使用 `urljoin()`；不得为了形式统一而强行改成 f-string。
7. 很短且只使用一次的 URL 字面量可以直接传入；较长或在同一代码块重复使用的 URL 必须优先复用现有变量，或提取为简短的局部变量。

## HTML基础写法

- HTML、JSON 及混合响应的解析必须遵守 `references/data-parsing.md`。
- 使用 `BeautifulSoup(resp.text, "html.parser")` 解析。
- 使用 `rows = soup.select(...)` 获取列表。
- 使用 `a_tag = row.select_one('a')` 获取链接元素。
- 对每个列表项，按“URL 构造与变量复用”生成绝对详情 URL。
- 紧接着使用 `is_same_origin_url()` 校验同源并过滤附件；优先复用语义正确的变量，不得使用可能不同源的接口 URL 作为比较基准。
- 非同源链接立即 `continue`；只有同源链接才继续提取标题、时间并执行 `ret_list.append()`。
- 使用 `get_text(strip=True)` 提取标题和发布时间。
- 每条 `ret_list.append()` 至少返回 `url`、`title`、`pubTime`。
- 返回或传递的 `title`、`pubTime` 必须遵守 `references/data-parsing.md` 的最终字段约束。


## HTML特殊情况1：列表页没有发布时间

- 如果列表页没有提供发布日期，或发布日期不完整，则将 `pubTime` 设置为 `None`。
- `get_content` 中必须使用 `if params['pubTime'] is None:` 补齐。
- 不要用空字符串、`''`、`'None'` 作为需要补齐的标记。

## HTML特殊情况2：列表标题被截断

- 列表标题末尾存在 `...`、`…`、`……` 等省略标记，并经详情页抽样或稳定页面结构确认是长度截断时，必须把 `title` 设置为 `None`，禁止返回或自行拼接截断标题。
- 判断只针对已经确认的尾部截断标记；不得因为标题中间包含省略号就认定标题不完整，也不得把真实标题自带的尾部省略号误判为截断。
- `get_content` 必须使用 `if params['title'] is None:` 从详情页标题元素或真实详情字段提取完整标题。


## HTML特殊情况3：发布时间包含其他文本

- 如果页面已经直接给出干净的纯日期、`YYYY-MM-DD HH:MM` 或 `YYYY-MM-DD HH:MM:SS`，必须原样提取，不要额外处理，也不必刻意构造或删除时、分、秒。
- 如果 `pubTime` 中包含 `发布时间：`、栏目名、来源等额外文本，必须使用 `handle_str.extract_and_validate_dates()` 提取其中的纯日期。


## HTML特殊情况4：发布时间分散在多个元素

- 如果日期分散在多个元素中，例如年/月在一个元素、日在另一个元素，可以分别提取后拼接。
- 拼接后必须形成可识别的完整日期，例如 `YYYY-mm-dd`。
- 这类场景没有固定模板，必须根据页面实际元素位置编写。


## HTML特殊情况5：多个栏目列表结构不一致

- 如果多个栏目共用 `get_list`，但列表页 HTML 结构、详情URL拼接方式、标题位置、发布时间位置等不一致，可以在 `payload_list` 中为每个栏目增加顶层 `t` 字段区分类型。
- 栏目类型区分字段必须只能使用顶层 `t`，禁止使用顶层 `type`、`category`、`kind`、`column` 等其他字段名。
- 顶层 `t` 字段必须在 `init_func` 中随 `start_urls` 一起传入，例如：`{'url': p['url'], 't': p['t']}`。
- `get_list` 中允许使用 `if params['t'] == 1:`、`if params['t'] == 2:` 这类分支分别解析。
- 如果多个栏目的提取规则一致，禁止为了栏目名称不同而添加分支，必须使用统一解析逻辑。
- 每个分支内部仍然必须保持简短清晰，并且每条 `ret_list.append()` 至少返回 `url`、`title`、`pubTime`。
- 无论哪个分支，`url` 都必须在 `get_list` 中生成为绝对 URL，并且必须使用 `is_same_origin_url()` 校验其与用户给出的目录网站 URL 同源。






## JSON特殊情况1：url 从接口中提取

1. 接口返回相对路径、根路径或完整 URL 时，使用 `urljoin()` 和语义正确的目录网站 URL 变量补全；接口只返回 ID 等字段且详情 URL 结构固定时，优先使用 f-string 直接生成完整 URL。
2. 得到完整 URL 后，必须使用 `is_same_origin_url()` 与用户给出的目录网站 URL 校验同源，并优先复用语义正确的现有变量或局部变量。
3. 接口 URL 只用于请求数据，不得代替用户给出的目录网站 URL 作为同源判断基准。

如果详情页正文请求依赖接口返回的 `id`、`articleId`、`projectId`、`noticeId`、`categoryId`、`detailUrl` 等参数，必须一并返回给 `get_content` 使用。


## JSON特殊情况2：接口返回时间戳

- 接口返回的日期是毫秒级时间戳时，使用 `handle_str.time_stamp(int(pubTime))` 转成 `YYYY-mm-dd HH:MM:SS`。
- 接口返回的日期是秒级时间戳时，必须先乘以 1000，再使用 `handle_str.time_stamp(int(pubTime) * 1000)`。
- 保留 `time_stamp()` 返回的日期时间，不得强制截断为纯日期。
- 不要添加额外异常判断，按接口实际返回格式直接转换。

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


## JSON特殊情况4：列表接口已包含正文 content

- 如果接口列表中已经包含正文内容，可以在 `get_list` 返回中带上 `content`。
- `content` 返回前应按实际情况使用 `handle_str.completion_url(str(content), params['url'])` 补全正文中的相对链接。
- 后续 `get_content` 中可使用 `if params.get('content'):` 判断，命中后可直接 `return params`，也可显式构造结果；只要返回字典包含 `title`、`pubTime`、`url`、`content` 四个必需字段即可。
- 这种情况下 `get_list` 返回字典必须已经包含 `url`、`title`、`pubTime`、`content`。

