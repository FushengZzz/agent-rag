# 联网工具

DeepSeek 提供两个服务端工具，在对话中提供与 DeepSeek 网页端相同的联网搜索、深度思考搜索与阅读链接。是否联网由模型判断，搜索和抓取都在服务端完成，客户端不需要执行任何工具。

这两个工具为对话场景设计，用于[构建 Chatbot](https://api-docs.deepseek.com/zh-cn/guides/build_a_chatbot.md)。如果要在 Agent 或自己的程序里搜索和抓取网页，请使用 [网页搜索与抓取](https://api-docs.deepseek.com/zh-cn/guides/search.md) 接口。

- **[联网搜索](#web-search)**：开启方式：声明 `deepseek_web_search`，关闭思考；说明：模型根据提问自动发起搜索，并附引用作答

- **[深度思考搜索](#search-while-thinking)**：开启方式：声明 `deepseek_web_search`，开启思考；说明：模型在多步推理中自主搜索、打开网页、页内查找，边推理边检索求证

- **[阅读链接](#read-links)**：开启方式：声明 `deepseek_read_url`；说明：模型自动识别用户消息中的链接，抓取网页内容并结合上下文作答

可在 Messages API、Responses API 与 Chat Completions API 中使用。本页大部分内容描述的是 Messages API 中的格式，另外两个协议中的格式见下文 [Responses API](#responses-api) 与 [Chat Completions API](#chat-completions-api)。

请使用 `deepseek-flash` 模型。

***

<a id="declare-tools"></a>

## 引用

回答引用了来源时，其 `text` 块带有 `citations`：

```json
{
  "type": "text",
  "text": "上海今天多云。",
  "citations": [
    {
      "type": "web_search_result_location",
      "url": "https://example.com/weather",
      "title": "...",
      "encrypted_index": "",
      "cited_text": "上海今天多云。"
    }
  ]
}
```

- 流式输出时，每条引用通过当前 `text` 块上的 `citations_delta` 事件下发。
- 一个 `text` 块带上引用后，之后的正文会另起一个新的 `text` 块，因此每个块的引用只对应它自己的文本。同一个块内同一 URL 最多出现一次。
- `type` 恒为 `web_search_result_location`，深度思考搜索中打开的网页也是如此。`cited_text` 是当前块截至该引用处的回答文本，不是从来源中摘录的原文。`encrypted_index` 恒为空字符串，`title` 可能为 `null`。
- 回传时会忽略引用。

***

## 用量与计费

最终 `message_delta`（或非流式响应）中的 `usage` 是整个请求的计费用量，按各步推理累加：

- **`input_tokens`**：未命中上下文缓存的输入 Token

- **`cache_read_input_tokens`**：命中上下文缓存的输入 Token

- **`output_tokens`**：输出 Token

- **`output_tokens_details.thinking_tokens`**：其中的思考 Token，开启思考时返回

- **`cache_creation_input_tokens`**：恒为 `0`

- **`server_tool_use.web_search_requests`、`web_fetch_requests`**：响应中搜索结果块、抓取结果块的数量（含错误块）

- **`server_tool_use.tool_search`、`tool_fetch`、`tool_image_search`**：搜索次数（不含图片搜索）、抓取次数、图片搜索次数

这些服务端工具不计费（文字搜索、图片搜索与网页抓取），只有模型 Token 用量计费。

***

## 错误

输入命中内容审核时返回 `400 Content Exists Risk`。请求的上下文超过模型上限时返回 `400`。

常见错误信息：

- **同一个工具声明了两次**：``tools: `deepseek_web_search` can only be declared once``

- **声明了其他服务端工具**：``tools: other tools cannot be used together with `deepseek_web_search`, `deepseek_read_url`, `safety_check` or `title` yet``

- **工具带有 `allowed_domains`、`blocked_domains` 或 `user_location`**：`` tools: `allowed_domains` is not supported by `deepseek_web_search` ``

- **`tool_choice` 指定了已声明的联网工具**：``tool_choice: `deepseek_web_search` cannot be forced``

- **`safety_check` 没有合法的 `level`**：`` safety_check: `level` must be `low` or `high` ``

- **要续写的回复使用过联网工具**：``messages: the last `assistant` message used `deepseek_web_search` or `deepseek_read_url` and cannot be continued; resend the previous request``

<a id="generation-failures"></a>

### 生成失败

回答开始生成之后出错时（例如推理超时或中断），HTTP 状态码已经是 `200`，响应以错误结束，并带上 `usage`。

- **Messages**：流式：以 `error` 事件结束，之后没有 `message_delta` 与 `message_stop`；非流式：响应体为 `{"type": "error", "error": {...}, "usage": {...}}`

- **Responses**：流式：以 `response.failed` 事件结束；非流式：`status` 为 `failed`，`error.code` 为 `server_error`

- **Chat Completions**：流式：最后一个 chunk 带有 `error`，`choices` 为空，之后没有 `[DONE]`；非流式：响应体为 `{"error": {...}, "usage": {...}}`

```text
event: error
data: {"type":"error","error":{"type":"api_error","message":"The model failed to generate a complete response. Please retry."},"usage":{...}}
```

非流式响应的状态码是 `200`，SDK 不会抛出异常，请检查响应体中的 `error`（Responses API 检查 `status`）。

***

<a id="responses-api"></a>
