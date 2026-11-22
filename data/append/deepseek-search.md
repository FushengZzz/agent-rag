# 网页搜索与抓取

Search 接口和 Fetch 接口为 Agent 与 RAG 应用提供实时网页内容：

- **Search 接口**按 query 搜索网页，返回结构化结果。该接口由 DeepSeek 自研搜索引擎提供支持。
- **Fetch 接口**抓取单个网页，以 Markdown 文本返回页面内容。

两者都是原始 JSON API，使用与 DeepSeek API 相同的 Bearer 鉴权。

如果要让模型在对话中自己搜索和阅读网页，请使用 [联网工具](https://api-docs.deepseek.com/zh-cn/guides/web_tools.md)。

Search 接口暂不支持图片搜索，后续会支持。目前图片搜索只能通过 [联网工具](https://api-docs.deepseek.com/zh-cn/guides/web_tools.md#image-search) 使用。

Base URL 为 `https://api.deepseek.com`：

| API    | Endpoint                                        |
| ------ | ----------------------------------------------- |
| Search | `POST https://api.deepseek.com/v1/tools/search` |
| Fetch  | `POST https://api.deepseek.com/v1/tools/fetch`  |

完整的请求与响应 Schema 请参考 [Search API Reference](https://api-docs.deepseek.com/zh-cn/api/search.md) 和 [Fetch API Reference](https://api-docs.deepseek.com/zh-cn/api/fetch.md)。

***

## 计费

Search API 和 Fetch API 按成功请求次数计费，不按 token 或返回结果条数计费：

| API        | 计费单位          | 价格 |
| ---------- | ------------- | -- |
| Search API | 每 1,000 次成功请求 | 5元 |
| Fetch API  | 每 1,000 次成功请求 | 5元 |

独立请求只有返回 HTTP 200 且产生结果时才会计费（Search 的 `results` 必须非空，Fetch 必须返回网页正文）。请求失败、搜索无结果或超时不计费。`count` 只控制返回的结果条数，不影响单次请求的价格。

模型通过服务端工具执行的搜索不计费（文字搜索、图片搜索与网页抓取），只有模型 Token 用量计费。服务端工具包括[联网工具](https://api-docs.deepseek.com/zh-cn/guides/web_tools.md#billing)、Responses API 的 `web_search`、Claude Code 的 Web Search，以及 DeepSeek Harness 中「网页搜索提供方」设为「DeepSeek 服务端搜索」或「自动」（默认值）时的搜索。

客户端直接调用 Search 与 Fetch API 的搜索按上表价格计费，例如 DeepSeek Harness 中「网页搜索提供方」为「DeepSeek Search API」时的搜索，以及 [Codex Alpha Search](https://api-docs.deepseek.com/zh-cn/quick_start/agent_integrations/codex.md)。

***

## 限速

对每个账号，Search 和 Fetch 分别独立限速，互不占用额度：

| API    | QPS 限制 |
| ------ | ------ |
| Search | 100    |
| Fetch  | 25     |

QPS（每秒请求数）限制按账号粒度计算，与使用哪个 API Key 无关，并与模型并发限制相互独立。超过账号级 QPS 限制的请求会收到 HTTP 429 错误码。除了账号级限制，Fetch 还针对目标域名有 QPS 限制，超过该限制也会收到 HTTP 429 错误码。
