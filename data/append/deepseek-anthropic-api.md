# 使用 Anthropic API

为了满足大家对 Anthropic API 生态的使用需求，我们的 API 新增了对 Anthropic API 格式的支持，其 `base_url` 为 `https://api.deepseek.com/anthropic`。

通过简单的配置，即可将 DeepSeek 的能力，接入到 Anthropic API 生态中。

请求参数、响应字段和完整 HTTP 示例请参考 [Messages API 参考文档](https://api-docs.deepseek.com/zh-cn/api/create-message.md)。

***

## 通过 Anthropic API 调用 DeepSeek 模型

1. 安装 Anthropic SDK

```
pip install anthropic
```

2. 配置环境变量

```
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_API_KEY=${YOUR_API_KEY}
```

3. 调用 API

**注意**：以 `claude` 开头的不支持的模型名仍会被接受：`claude-opus*` 会映射到 `deepseek-v4-pro`，其它 `claude*` 模型名会映射到 `deepseek-flash`。不以 `claude` 开头的未知模型名会返回 `400` 错误。

***

## Anthropic 模型映射

您在使用 Anthropic API 时，我们会对您传入的 claude 模型名进行映射：

- claude-opus 开头的模型，会映射到 `deepseek-v4-pro`
- claude-haiku、claude-sonnet 开头的模型，会映射到 `deepseek-flash`

claude-opus 映射到的 `deepseek-v4-pro` 按 V4 Pro 价格计费。

通过这样的映射，您在使用新版 Claude Desktop APP 的 developer 模式时，可以绕过 APP 对模型名的限制，只需改动 base\_url 和 api\_key，即可在其中接入 DeepSeek 模型。

***

### 简单字段

- **model**：改为使用 DeepSeek 模型

- **max\_tokens**：支持。在 HTTP 请求中可省略，默认值和有效上限取决于模型、思考模式与推理强度。Anthropic SDK 要求提供此参数，因此 SDK 示例显式设置该值。兼容场景的例外见下文

- **container**：忽略

- **mcp\_servers**：忽略

- **metadata**：支持 `user_id`，其它字段忽略 / 关于 `user_id` 参数的更多信息，请参考 [限速与隔离](https://api-docs.deepseek.com/zh-cn/quick_start/rate_limit.md)。

- **service\_tier**：忽略

- **stop\_sequences**：完全支持。最多 16 个非空字符串，每个字符串不能超过 512 字节（UTF-8 编码）

- **stream**：完全支持

- **system**：完全支持

- **temperature**：有效范围为 \[0.0 \~ 2.0]。非思考模式下生效；思考模式下固定为 `1.0`

- **thinking**：支持 `type: "enabled"` 和 `type: "disabled"`；`adaptive` 按 `enabled` 处理。`budget_tokens` 被忽略

- **output\_config**：仅支持 `effort`

- **top\_k**：忽略

- **top\_p**：因模型而异： / `deepseek-flash`：思考模式下生效（下限 `0.95`），非思考模式下恒为 `1.0`。 / `deepseek-v4-pro`：思考模式下忽略传入值（启用工具调用时固定为 `0.95`，否则为 `1.0`），非思考模式下生效。即使提供了 `tools`，将 `tool_choice` 设为 `{"type": "none"}` 也会关闭工具调用

- **safety\_check**：DeepSeek 扩展字段。`{"level": "high"}` 开启内容安全审核，`low` 或不传则不开启，见 [模型内容安全](https://api-docs.deepseek.com/zh-cn/guides/safety.md)

- **title**：DeepSeek 扩展字段。`{"enabled": true}` 返回会话标题，见 [会话标题](https://api-docs.deepseek.com/zh-cn/guides/conversation_title.md)

在部分 Claude Code 或 OpenCode 主 Agent 的思考模式请求中，兼容处理可能将实际生效的 `max_tokens` 提高到请求值以上。在这些场景下，不能依靠此参数严格限制输出 token 数。
