# get_content 方法约束

真实案例统一按 `SKILL.md` 的“真实案例检索目录路由表”查找，本文件只维护 `get_content` 的完整方法约束，不维护案例路径。

## 方法接口与返回值

- 形参名固定为 `params`，禁止修改、增加或删除形参。
- 正常返回包含 `title`、`pubTime`、`url`、`content` 的字典；HTTP 状态码为 4xx 或 5xx 时返回 `None`。
- `content` 有 HTML 源码时返回 HTML 字符串，否则返回文本内容。
- 禁止添加无依据的异常捕获，保持代码简洁、易读。

## URL 构造

- 详情接口或附件接口的 URL 结构固定、只需插入 `params` 中的 ID 或其他字段时，优先使用一个清晰的 f-string 直接生成完整 URL。
- 能用一个 f-string 表达时，禁止使用字符串相加、多段括号字符串、`format()`，也不要先构造相对字符串再调用 `urljoin()`。
- 只有源数据提供相对路径、根路径或完整 URL，需要进行标准 URL 补全时才使用 `urljoin()`。
- 较长或重复使用的基准 URL 优先复用语义正确的现有变量；没有可复用变量时使用局部变量，禁止新增全局 URL 常量。



## HTML基础写法

- HTML、JSON、混合响应以及最终字段处理必须遵守 `references/data-parsing.md`。
- 确认瑞数时，详情请求前必须按 `references/ruishu.md` 调用 `get_cookies()`；返回 `None` 时返回 `None`，成功时把本次 Cookie 传给详情请求。
- 确认加速乐时，必须按 `references/jsl.md` 使用 `agent_pool` 和固定 challenge 流程取得代理与 Cookie；8 次失败后返回 `None`，成功后使用局部 Cookie 请求头和同一个代理发送详情请求。
- 确认阿里 `acw_sc__v2` 时，必须按 `references/acw-sc-v2.md` 使用 `agent_pool` 和固定 Cookie 流程；8 次失败后返回 `None`，成功后通过 `cookies=cookies` 和同一个代理发送详情请求。
- 使用 `auto_request(url=params['url'], headers=HEADERS, cookies=COOKIES)` 请求详情页。
- 使用 `BeautifulSoup(resp.text, "html.parser")` 解析详情页。
- 使用 `content = soup.select_one(...)` 定位正文元素。
- 返回前使用 `handle_str.completion_url(str(content), params['url'])`。
- 返回字典使用 `params['title']`、`params['pubTime']`、`params['url']` 和处理后的 `content`。
- HTML 正文必须精确定位正文主体，禁止返回整页 HTML、列表页 HTML或包含大量导航、页脚、侧栏的外层节点。
- 最终 `url` 必须保持文章详情页 URL；正文来自独立接口时不得用接口 URL 替换。


## 特殊情况处理方式

分析详情数据时可能遇到以下特殊情况，必须按照对应要求编写代码。

### 详情页补齐 pubTime

- 如果 `get_list` 中 `pubTime` 为 `None`，必须在 `get_content` 中补齐。
- 判断方式固定使用 `if params['pubTime'] is None:`。
- 如果详情页直接提供干净的纯日期、`YYYY-MM-DD HH:MM` 或 `YYYY-MM-DD HH:MM:SS`，必须原样提取，不要额外处理，也不必刻意构造或删除时、分、秒。
- 如果详情页发布时间文本包含 `发布时间：`、栏目名、来源等额外内容，必须使用 `handle_str.extract_and_validate_dates()` 提取其中的纯日期。


### get_list 已经提取 content

- 如果 `get_list` 已经提取正文内容，并且返回字典已包含 `url`、`title`、`pubTime`、`content`，则 `get_content` 不再发起请求，可以直接返回 `params`。
- 固定写法：

```python
if params.get('content'):
    return params
```


### 详情页补齐 title

- 如果列表页缺少标题，或列表标题以经确认的 `...`、`…`、`……` 等省略标记结尾而被截断，`get_list` 必须传入 `title=None`，并在 `get_content` 中补齐。
- 判断方式固定使用 `if params['title'] is None:`。
- 必须从详情页的完整标题元素或详情接口真实标题字段提取，禁止对列表截断文本进行猜测、删除省略号或人工补字。
- 补齐后按 `references/data-parsing.md` 清理标题，并仍然返回 `params['title']`。


### 额外附件按抽样结果生成

- 分析阶段必须按用户指定的采集页数执行附件抽样：只采集 `1` 页时，仅在第一页的同源列表项中随机抽取 `3` 条详情页；采集多页时，必须在每个指定页分别随机抽取 `3` 条同源详情页。任一页不足 `3` 条同源列表项时，必须检查该页全部实际可用条目。
- 只有抽样确认存在额外附件下载入口时，才在 `get_content` 中生成附件提取和追加代码。附件判断必须依据附件区、下载文本、`download` 属性、附件接口、实际点击或响应等已验证语义，禁止只按 URL 后缀或文件名筛选。
- 已确认是附件下载链接时，无论 URL 是动态接口、参数地址、无扩展名地址还是重定向地址，都必须保留；禁止因为 URL 或文件名不含 `.pdf`、`.doc`、`.docx`、`.xls`、`.xlsx` 而丢弃。
- 附件提取必须使用抽样确认的具体 DOM 或 JSON 字段，禁止在未发现附件时生成遍历所有 `<a>` 的猜测性代码。

#### 附件追加方式

1. 精准定位的 `ul`、`div` 或其他外层附件容器已经只包含本条内容的全部附件下载链接时，优先直接把该容器追加到 `content`；不要刻意逐个提取附件并重新构造 `<a>` 标签。
2. 直接追加外层容器前，必须确认其中链接都是已经验证的附件下载入口，且没有混入导航、分享、正文推荐等非附件链接。
3. 附件链接默认按同源处理，不检查、不比较也不区分其域名。只要容器满足前述条件，就直接追加整个容器，不得因附件 URL 的域名不同改为逐个构造 `<a>` 标签。
4. `href` 已是完整绝对 URL 时原样保留；`href` 是相对路径时，追加容器后统一通过 `completion_url()` 和当前详情页 URL 补全。最终 `content` 中的附件链接必须是完整、可直接下载的 URL。
5. 附件链接不是实际下载地址，而是 JavaScript 调用、按钮参数、中间接口或需要换取真实地址时，必须先还原真实下载 URL，再逐个构造 `<a>` 标签；是否构造只由链接形态决定，与域名无关。


### 正文为内嵌 PDF

- 如果正文通过 `iframe`、`object`、`embed` 展示 PDF，必须从 `src` 或 `data` 等实际属性提取真实 PDF URL，使用 `soup.new_tag('a', href=..., string='内容附件')` 转换为链接并追加到 `content`。
- 原 `iframe`、`object`、`embed` 标签如果不再有保留价值，可以在追加 `<a>` 后使用 `decompose()` 移除。

### PDF URL 存在于 JavaScript

- 必须先使用 BeautifulSoup 定位正文或相关 `script` 标签。只有脚本参数无法用 BeautifulSoup 直接提取时，才允许对该局部内容使用 `re`。
- 提取 PDF URL 后，使用 `soup.new_tag()` 创建带“内容附件”标识的 `<a>` 标签并追加到 `content`。
- 如果页面还存在独立附件区，必须同时追加该附件区，不得因已提取 PDF 而忽略其他附件。

### 正文来自 JavaScript 渲染

- 只在分析确认正文由 JavaScript 将接口 JSON 渲染为页面 DOM 时，才允许使用 `request.render_page`。
- 编码前必须完整阅读 `references/framework-functions.md` 的 `render_page` 小节，并从 `examples/render_content/` 中只读取与目标页面渲染链路最接近的少量案例。
- 按已确认的真实渲染链调用 `request.render_page(url=..., sleep_time=...)`。`sleep_time` 固定设置3000。
- `render_page` 返回渲染后的 HTML 字符串，可使用 `BeautifulSoup` 解析。
- 渲染失败时的重试、等待和失败返回方式只按目标站点已验证行为及最接近案例编写，禁止无依据照搬异常捕获或重试逻辑。
- 除 `request.render_page` 这一已确认的渲染请求外，列表、详情接口、附件接口及其他业务请求仍必须使用 `auto_request`。

### 正文接口依赖列表页参数

- 列表页和详情页都是 JSON 接口时，`get_list` 可以把详情接口需要的 `id`、`articleId`、`projectId`、`noticeId`、`categoryId`、`detailUrl`、`detail_url` 等参数一并返回。
- `get_content` 必须直接从 `params` 中读取这些参数，用来拼接详情接口URL、查询参数、`data` 或 `json`。
- `params['url']` 始终表示文章详情页URL。
- 只有文章详情页URL本身就是 JSON 详情接口时，才直接使用 `params['url']` 请求正文。
- 如果实际请求正文的是另一个 JSON 详情接口，应新建局部变量 `url` 或使用 `params['detail_url']` 请求详情接口，最终返回结果中的 `url` 仍使用 `params['url']`。


### 以表单或载荷形式请求正文接口

- 如果详情接口需要 `data` 或 `json`，则在 `get_content` 中从 `params` 取列表页返回的字段组装请求参数。
- 需要发起业务请求时必须使用 `auto_request`；列表接口已提供完整正文时不得重复请求。
- 如果详情请求参数来自任务字典中的统一请求参数容器，该容器仍必须命名为 `data`；发送时再按真实请求映射为 GET `params`、POST `data` 或 POST `json`。
- `data`、`params` 和 `json` 只表示请求参数容器及其发送映射，不作为栏目分支判断依据。

### 列表接口已包含正文 content

- 如果 `get_list` 已经返回 `content`，`get_content` 不需要再次请求详情页。
- `params` 必须已经包含 `url`、`title`、`pubTime`、`content`。
- 固定写法：

```python
if params.get('content'):
    return params
```

