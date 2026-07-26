# init_func 方法约束

`init_func` 使用 `payload_list` 描述栏目、列表 URL、页数和请求参数，并把全部列表页任务写入 `start_urls`。参考真实案例统一按 `SKILL.md` 的“真实案例检索目录路由表”查找，本文件不维护案例路径。

## 方法职责

1. `init_func` 必须保留为 `@classmethod`，禁止修改方法名和签名。
2. 只负责组织列表任务，不在此方法请求或解析页面。
3. 多个栏目无论结构是否一致，都在同一个 `payload_list` 中描述。

## payload_list

1. `payload_list` 必须是元组，每个元素必须是字典。
2. 每个任务字典必须包含：
   - `url`：列表页或列表接口的绝对 URL，禁止只写域名或提取为全局变量。
   - `page_number`：采集页数，字段名固定，值必须是 `int`。
3. 每个任务字典前使用 `#` 注释标明栏目，例如 `# 通知公告`。
4. 只有多个栏目的 HTML 结构、接口字段、详情 URL 拼接或分页处理确实不同时，才允许增加顶层 `t` 供 `get_list` 分支；栏目类型字段只能命名为 `t`。

## 请求参数容器

1. `payload_list` 和 `start_urls` 中的请求参数只能放在顶层 `data`，禁止使用顶层 `params`、`json`、`body`、`form` 等字段。
2. `data` 是任务字典统一的请求参数容器，不表示实际请求一定是 POST 表单。
3. 写入 `start_urls` 时必须使用 `p['data'].copy()`，避免分页任务共享并修改同一个字典。
4. `get_list` 再按真实请求方式映射：GET 查询参数用 `params=params['data']`，POST 表单用 `data=params['data']`，POST JSON 用 `json=params['data']`。

## start_urls 生成

1. 通常使用两个嵌套 `for` 循环遍历 `payload_list` 和页码，将全部任务写入 `cls.start_urls`。
2. URL 分页、参数分页以及第一页与后续页规律不同的情况，都必须在嵌套循环内按真实规律处理。
3. URL 模板、字符串替换或 `data` 页码更新方式必须来自实际分页请求，禁止假设页码从 0 或 1 开始。
4. 使用顶层 `t` 时，将其随任务一起写入 `start_urls`；存在 `data` 时同时传入复制后的参数字典。
5. 只采集一页时可以直接写入唯一任务，但仍应保持 `payload_list`、栏目注释和字段命名一致；不得为此伪造分页 URL。
6. 分页 URL 的固定结构已经明确、只需插入 `index` 时，优先使用 f-string；禁止使用字符串相加、多段括号字符串或不必要的 `format()`。只有第一页与后续页规律不同，或 URL 不是简单插值关系时，才按真实规律使用条件分支或其他清晰写法。

## 简化模板

无请求参数：

```python
@classmethod
def init_func(cls):
    payload_list = (
        # 通知公告
        {
            "url": "实际列表页绝对 URL",
            "page_number": 1,
        },
    )

    for p in payload_list:
        for index in range(1, p['page_number'] + 1):
            cls.start_urls.append({'url': p['url']})
```

存在请求参数：

```python
@classmethod
def init_func(cls):
    payload_list = (
        # 通知公告
        {
            "url": "实际列表接口绝对 URL",
            "page_number": 1,
            "data": {
                "page": 1,
            },
        },
    )

    for p in payload_list:
        for index in range(1, p['page_number'] + 1):
            data = p['data'].copy()
            data['page'] = index
            cls.start_urls.append({'url': p['url'], 'data': data})
```

模板中的 URL、分页字段和更新方式仅展示结构，必须替换为目标站点已经验证的真实值。
