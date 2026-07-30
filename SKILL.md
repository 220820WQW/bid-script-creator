---
name: bid-script-creator
description: 根据用户提供的目标网址、招投标栏目和采集页数，分析列表页与详情页的真实 HTML 或 JSON 数据来源，在参考现有真实案例后，生成符合 bbSpider 框架约束的单文件 Python 采集脚本；脚本用于采集同源详情页的 url、title、pubTime、content 及可下载附件。
---

# 招投标脚本生成器

## 核心目标

根据用户提供的目标站点、栏目和采集页数，分析真实数据来源，生成完整、独立的 bbSpider 单文件 Python 采集脚本。采集字段包括 `title`、`url`、`pubTime`、`content`，及可下载附件。



## 最高优先级约束

1. 禁止删除或修改 `bbSpider` 框架及无关文件。逆向分析文件只能临时存放，不得作为额外交付物写入脚本目录。
2. 禁止运行完整采集脚本。只允许使用 `ast.parse` 进行语法检查。
3. 脚本中的所有业务网络请求必须使用固定 `auto_request`，包括列表、详情、正文接口和附件接口请求；禁止使用其他网络库发包。瑞数、加速乐和阿里 `acw_sc__v2` 的 Cookie/challenge 前置流程必须严格遵守各自特殊 reference，其固定请求不适用本条业务请求约束。
4. 禁止把栏目 URL、分页 URL、详情 URL或接口 URL 提取为全局变量。代码保持简洁，禁止无意义的封装、类型注解和通用化。
5. 禁止猜测请求 URL、请求参数、分页规律、选择器、JSON 字段、详情正文或附件结构；所有站点实现必须来自真实分析结果。
6. 编码前必须明确区分已确认事实和未确认事项。任何不确定内容，必须向用户说明不确定点并询问，禁止猜测、静默选择或用推测性兜底代替确认。
7. 生成脚本时都必须以“用最少的代码解决当前问题”为最高实现原则：只保留完成真实采集流程不可缺少的代码，能直接表达就不封装，能复用现有值就不重复构造。
8. 实际使用公共函数或辅助函数前，必须到 `references/framework-functions.md` 阅读对应函数小节。
9. 开始前必须先阅读 `references/contract.md` 熟悉脚本模板和框架契约。



## 全局代码约束

1. 全局作用域只保留固定基础导包、站点实现确需的最少导包，以及从主流程入口实际调用到的函数和常量。
2. 同一种站点能力只保留一个语义明确的全局入口，例如 `encrypt_request_data()`、`decrypt_response_data()` 或 `build_request_sign()`；入口可调用实现必需的内部函数。
3. 禁止照搬完整 JS 库、通用加密库、调试代码、测试数据、未使用分支或无关工具函数。只使用一次且能简洁表达的逻辑直接写入入口函数。
4. `HEADERS`、`COOKIES` 默认为空字典。简单固定校验值可直接写入；动态请求头或 Cookie 不得硬编码。
5. 只允许新增被主流程实际使用的固定加密、解密、签名、特殊数据还原入口，以及必要的 `KEY`、`IV`、`PUBLIC_KEY`、固定盐值等大写常量。
6. 执行 `references/contract.md` 的最简优先约束；清除重复计算、重复分支、无意义中间层和非必要注释，但不得删改特殊案例要求的固定代码。
7. 修改已有脚本时只触及当前任务必需的代码，禁止顺便重构、格式化或清理无关内容；只清理由本次修改直接产生的未使用代码。



## 生成前必须读取

完成目标网页分析后、写入任何 Python 代码前，必须完整读取：

1. `references/init-func.md`
2. `references/get-list.md`
3. `references/get-content.md`

分析和生成过程中按职责读取：

| 时机 | 必须读取 | 内容 |
|---|---|---|
| 开始分析目标站点前 | `references/site-analysis.md` | 网页分析、数据来源确认、附件抽样和停止条件 |
| 确定 HTML、JSON 或混合响应解析方式时 | `references/data-parsing.md` | 数据解析及最终 `title`、`pubTime` 约束 |
| 生成三个核心方法前 | `references/init-func.md`、`references/get-list.md`、`references/get-content.md` | 各方法的完整接口和实现约束 |

不得只根据案例生成代码，也不得以找到相似案例代替读取上述 reference。



## 工作流程

必须严格按以下顺序执行。

### 1.确认用户需求

确认以下最小必要信息：

- `输出文件`：最终生成/修改的python文件名称。
- `目标网址`：列表页入口或站点首页 URL。
- `列表页栏目`：需要采集的栏目名称。
- `页数`：每个栏目对应的采集页数。

多个网址或栏目先整理为：

```text
输出文件：[文件名]
采集任务：
1. 网址：[URL]；栏目：[栏目名]；页数：[N]
...
```

- 缺少输出文件或目标网址时必须询问；
- 栏目无法从明确列表页和用户描述中判断时必须询问用户。



### 2.分析目标网页

完整遵守 `references/site-analysis.md`：

1. 逐个确认栏目入口、分页规律和列表数据来源。
2. 确认详情链接、标题、发布时间、正文和附件的真实 DOM 或 JSON 字段。
3. 动态栏目必须逐栏目完成浏览器点击与网络请求联调。
4. 按用户指定页数完成同源详情页和附件抽样。
5. 记录生成脚本所需的请求方式、参数映射、字段路径和栏目差异。
6. 命中瑞数、加速乐和阿里acw_sc__v2后必须按各自特殊 reference 执行。



### 3.生成脚本代码

1. 完整读取“生成前必须读取”列出的三个核心 reference。
2. 确认不存在会改变实现路径的未解决歧义。
3. 根据下表检索最接近的少量真实案例。
4. 严格根据 step2 的真实结果依次生成 `init_func`、`get_list`、`get_content`。



## 真实案例检索目录路由表

先完成 step2，再按已经确认的实现特征选择目录。命中多个特征时可以依次检索多个目录；优先检索对主代码路径影响最大的特殊特征，未找到接近案例时回退到 `examples/common-cases/`。

| 判断条件 | 优先检索目录 | 建议检索特征 |
|---|---|---|
| 普通 HTML、普通 JSON、HTML/JSON 混合、JSON 字段包含 HTML | `examples/common-cases/` | 请求方式、分页参数、`BeautifulSoup`、`resp.json()`、字段路径、正文来源 |
| 列表数据来自页面 `datastore` 或同类内嵌数据块 | `examples/list-datastore/` | `datastore`、内嵌 JSON、列表数据变量名、解析入口 |
| 列表项或正文依赖 `document.write()` 生成 | `examples/document-write/` | `document.write`、脚本字符串、局部 HTML 还原 |
| 列表响应已经包含完整正文，`get_list` 可直接返回 `content` | `examples/list-with-content/` | `content`、`if params.get('content')`、直接返回 `params` |
| 标题与发布时间位于同一元素、子元素或同一段文本 | `examples/title-pubtime-mixed/` | 标题时间分离、子元素移除、固定分隔关系、纯标题 |
| 发布时间分散在多个元素或字段，需要组合完整日期 | `examples/pubtime-composed/` | 年月日分散、字段拼接、元素组合 |
| 列表页缺少或只有不完整发布时间，需要详情页补齐 | `examples/content-fill-pubtime/` | `pubTime: None`、`params['pubTime'] is None`、详情页日期 |
| 列表页缺少标题，或标题末尾存在经确认的省略标记而被截断，需要详情页补齐 | `examples/content-fill-title/` | `title: None`、`...`、`…`、`params['title'] is None`、详情页完整标题 |
| 多个栏目 HTML 结构、JSON 字段或 URL 规律不同，需要顶层 `t` 分支 | `examples/multi-layout-branch/` | `t`、多栏目分支、不同选择器、不同字段路径 |
| 正文通过 `iframe`、`object`、`embed` 或 JavaScript 展示 PDF 等内容文件 | `examples/embedded-content-file/` | `iframe`、`object`、`embed`、局部 JavaScript、PDF URL、`soup.new_tag` |
| 正文主体之外存在附件区、附件列表或附件接口 | `examples/extra-attachments/` | 附件容器、下载语义、动态下载地址、附件接口、完整下载链接 |
| 存在请求加密、响应解密、签名、动态 Cookie/Token 或特殊请求链 | `examples/crypto-request-flow/` | `encrypt`、`decrypt`、`sign`、`token`、`cookie`、`AES`、`RSA`、`MD5` |
| 命中瑞数，且浏览器 MCP 可以正常加载栏目页面 | `examples/ruishu/` | 202、`$_ts`、外链 JavaScript、`get_cookies`、`general_cookie`、`acquire_subjoin_path` |
| 命中加速乐，且浏览器 MCP 可以正常加载栏目页面 | `examples/jsl/` | 521、`__jsluid_s`、`__jsl_clearance_s`、`agent_pool`、Node、challenge |
| 命中阿里 `acw_sc__v2`，且浏览器 MCP 可以正常加载栏目页面 | `examples/acw_sc__v2/` | `acw_tc`、`renderData`、`arg1`、`aliyunwaf_`、`compute_cookie.js`、`agent_pool` |



### 案例选择规则

1. `examples` 按脚本的主要特征分类；脚本中可能具有其他案例特征，必须以当前所在目录为准。
2. 检索优先级顺序（特殊案例除外）：当前匹配案例特征目录 -> `common-cases` -> `other-cases`。
   - 如果未匹配到：`common-cases` -> `other-cases`。
3. 命中瑞数、加速乐或阿里 `acw_sc__v2` 时，固定优先检索各自特殊目录，不得改去通用加密目录套用其他流程。
4. 先用请求方式、分页方式、响应类型、字段路径、正文来源和特殊能力关键词缩小范围；每次只读取一个或少量最接近案例，禁止逐个读取整个目录。
5. 不要求存在完全匹配或唯一主案例。特殊目录没有接近案例时检索 `common-cases`；仍未找到时依据已验证事实和契约继续生成，不得因此停止或猜测。
6. 个别特殊案例放入 `other-cases`。
7. 案例只可参考方法契约、特殊场景写法和代码风格。禁止复制案例中的站点参数、选择器、字段、失效参数、错误写法或无用代码。



## 交付前检查

1. 只生成或修改用户指定的一个 Python 脚本，未修改框架和无关文件。
2. 请求方式、分页、字段、选择器、URL、正文和附件均有目标站点真实依据。
3. 代码已经过最简性检查：除特殊案例固定代码外，没有可删除的重复逻辑、无依据分支、无意义封装、重复构造或非必要注释，并且仍能清楚表达真实采集流程。
4. 未加入用户未要求、目标站点未使用的功能、配置、兼容分支、备用选择器或推测性兜底。
5. 每段站点相关代码均可追溯到明确依据，且没有会改变实现结果的未确认事项。
