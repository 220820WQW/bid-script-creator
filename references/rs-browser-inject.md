# 瑞数站点 Chrome MCP 浏览器注入测试 Prompt

请使用 MCP 连接已开启远程调试的 Chrome，并严格按照以下 CDP 流程打开目标瑞数站点。不要复用已有页面作为目标页面，不要省略全局预注入步骤。

## 操作要求

### 步骤 1：注册全局预注入脚本

在创建目标标签页之前执行 CDP 命令 `Page.addScriptToEvaluateOnNewDocument`，确保脚本在新页面的任何站点 JavaScript 运行前执行。

注入代码：

```javascript
// CDP 新建文档前置反自动化特征消除
(function () {
  try {
    delete navigator.cdc_adoQpoasnfa76pfcZLmcfl_Array;
    delete navigator.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
    delete navigator.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
    delete navigator.cdc_adoQpoasnfa76pfcZLmcfl_Object;
    delete navigator.cdc_adoQpoasnfa76pfcZLmcfl_Function;
    delete navigator.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;

    Object.defineProperty(navigator, "webdriver", {
      get: () => undefined,
      configurable: true
    });

    // 屏蔽自动化权限查询特征
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = function (parameters) {
      if (parameters.name === "notifications") {
        return Promise.resolve({ state: "prompt" });
      }
      return originalQuery.call(window.navigator.permissions, parameters);
    };
  } catch (e) {}
})();
```

注意：如果 MCP 将浏览器级 CDP 会话和页面级 CDP 会话分开，应确保该预注入脚本对后续新建的目标页面生效。必要时在新 `targetId` 对应的页面会话中再次注册，然后重新导航，不能在页面加载完成后才执行普通 `Runtime.evaluate` 来代替预注入。

### 步骤 2：创建全新独立标签页

执行：

```text
Target.createTarget
```

参数使用空白页：

```json
{
  "url": "about:blank"
}
```

等待命令返回新的 `targetId`。后续的页面导航、前台激活、JavaScript 执行、DOM 检查和网络监听都必须绑定到该新页面，不得误用原有标签页。

如果工具要求先附加目标，执行：

```text
Target.attachToTarget
```

参数：

```json
{
  "targetId": "{{NEW_TARGET_ID}}",
  "flatten": true
}
```

保存返回的 `sessionId`，后续页面级 CDP 命令通过该会话发送。

### 步骤 3：将新页面置于前台

执行：

```text
Page.bringToFront
```

确保新标签页处于激活和前台状态，以模拟用户主动打开标签页，并避免页面因后台状态进入休眠或降频。

如果当前 MCP 仅支持目标级激活，也可以使用：

```text
Target.activateTarget
```

参数：

```json
{
  "targetId": "{{NEW_TARGET_ID}}"
}
```

### 步骤 4：短暂等待

前台激活后等待约 `600ms`，再执行目标网址导航。

### 步骤 5：导航到目标瑞数网址

在新标签页对应的页面会话中执行：

```text
Page.navigate
```

参数：

```json
{
  "url": "{{TARGET_URL}}"
}
```

等待页面触发 `Page.loadEventFired`，或等待页面网络和 DOM 基本稳定。不要在瑞数挑战尚未完成时立即判定页面加载失败。

## 测试与检查

页面加载后执行以下检查：

1. 获取 `location.href`、`document.title` 和页面主要可见文本，确认最终页面仍是目标网址且栏目内容已显示。
2. 检查 `navigator.webdriver`，预期结果为 `undefined`。
3. 检查页面是否仍停留在验证页、空白页、异常提示页或 412/202 挑战内容。
4. 开启并检查网络请求，记录目标文档、XHR 和 Fetch 请求的 URL、请求方式、状态码及必要参数。
5. 如果接口 URL 包含 `RWEXzlB0`，记录完整请求，同时测试去掉该参数后、携带浏览器生成的瑞数 Cookie 是否可以直接获得明文响应。
6. 获取当前目标域 Cookie，用于验证瑞数挑战是否已经成功生成业务请求所需 Cookie；不得把本次浏览器中的动态 Cookie 硬编码进最终采集脚本。
7. 如果页面正常显示列表，继续检查真实列表 DOM、详情链接、标题、发布时间、分页请求、详情正文和附件结构。

可使用以下页面检查表达式：

```javascript
JSON.stringify({
  url: location.href,
  title: document.title,
  webdriver: navigator.webdriver,
  readyState: document.readyState,
  text: document.body ? document.body.innerText.slice(0, 5000) : "",
  cookies: document.cookie
});
```

## 异常处理

- 如果页面为空白或持续停留在挑战页，先确认预注入脚本是否确实在目标页面任何 JavaScript 运行前生效。
- 如果预注入脚本只注册在旧页面会话中，应在新目标会话重新注册，并重新创建或重新导航目标页。
- 如果新页面未激活，重新执行 `Page.bringToFront` 或 `Target.activateTarget`，等待 `600ms` 后再次导航。
- 如果页面能够正常展示，但普通 HTTP 请求返回 412 或挑战 HTML，应保留“浏览器分析、瑞数 Cookie 流程”的实现路径，不能因此直接判定站点不可采集。
- 不要通过页面加载完成后的普通 JavaScript 注入伪装成“新文档前置注入”；两者执行时机不同。

## 输出结果

完成后汇报：

1. 新建的 `targetId`，以及是否使用独立 `sessionId`。
2. 预注入命令是否在导航前成功注册。
3. 页面最终 URL、标题、加载状态和栏目可见性。
4. `navigator.webdriver` 的检查结果。
5. 瑞数挑战是否通过，以及目标域生成的 Cookie 名称（只汇报名称，不输出敏感 Cookie 值）。
6. 捕获到的列表或业务接口，以及去掉 `RWEXzlB0` 后的明文请求测试结果。
7. 若失败，明确失败发生在哪个步骤及已验证的原因。
