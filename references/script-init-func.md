# init_func方法的写入规则



## 基础用写法

真实案例见：`examples/general-cases/宁蒗彝族自治县人民政府(1)_招标(1)_1.py`



## URL传参

真实案例见：`examples/general-cases/淮河能源采购网(1)_招标(1)_1.py`



## URL传参多页规律不一致

示例2：采集多页时，第一页和其他页规律不一致

- 第一页url：https://www.gdmudgah.cn/h_gdykfsyy/Zhaobiaotoubiao/newslist.shtml
- 第二页url：https://www.gdmudgah.cn/h_gdykfsyy/Zhaobiaotoubiao/newslist_2.shtml

真实案例，见：`examples/general-cases/广东医科大学附属东莞第一医院(3)_招标(1)_1.py`



## data传参

页数由 `data` 中的参数控制。

- 【硬性规则】`payload_list` 中的请求参数只能保存在顶层 `data` 字段中。即使真实请求使用 GET 查询参数或 POST JSON，也禁止在 `payload_list` 中使用顶层 `params` 或 `json` 字段。
- 【硬性规则】向 `start_urls` 传入请求参数时，必须使用 `p['data'].copy()`。
- `data` 是任务字典中统一的请求参数容器，不代表实际 HTTP 请求一定使用 POST 表单。`get_list` 发送请求时必须再按真实请求映射为 GET `params`、POST `data` 或 POST `json`。

真实案例见：`examples/general-cases/云南云菌科技（集团）有限公司(1)_招标(1)_1.py`



以上三个示例，是常用的几个示例，不同的栏目，其规则可能不一致，但都要在  `for` 循环中，完成向 `start_urls` 中完成全部请求URL的输入。



特殊情况：如果只采集一页的情况下，可以直接向 `start_urls` 中传入数据，不必再去修改URL。示例：

```python
class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 通知公告
            {
                "url": "https://www.sbkj.com/tzgg/?pageNum=1",
                "page_number": 1,
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'],
                    }
                )

    def get_list(self, params: dict):
        ...

    def get_content(self, params: dict):
        ..
```

有 `data` 传参也是一样的：

```python
class CrawlerObject(Spider):
    start_urls = []
    data_category = 0
    collect_thread_number = 2
    is_upload_data = 0
    filter_type = "url"

    @classmethod
    def init_func(cls):
        payload_list = (
            # 通知公告
            {
                "url": "https://www.sbkj.com/api/tzgg/",
                "page_number": 1,
                "t": 1,
                "data": {
                    "page": "1",
                    "type": "tzgg"
                }
            },
        )

        for p in payload_list:
            for index in range(1, p['page_number'] + 1):
                cls.start_urls.append(
                    {
                        'url': p['url'], 'data': p['data'].copy(), 't': p['t']
                    }
                )

    def get_list(self, params: dict):
        ...

    def get_content(self, params: dict):
        ...
```






