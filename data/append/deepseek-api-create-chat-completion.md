# Chat Completions API
## 接口

```http
POST /chat/completions
```

operationId: `createChatCompletion`

### 服务地址

- `https://api.deepseek.com`

## 身份验证

### 验证方式 1

**bearerAuth**

`Authorization: Bearer <API_KEY>`

```yaml
type: http
scheme: bearer
```

## 请求体

**必填**

### application/json

- 引用: [CreateChatCompletionRequest](#schema-create-chat-completion-request) (`#/components/schemas/CreateChatCompletionRequest`)

### schema-create-chat-completion-request

**CreateChatCompletionRequest** — `#/components/schemas/CreateChatCompletionRequest`

- **字段**

  - **`messages`** (必填)

    对话的消息列表。

    - **数组元素**

      - 引用: [ChatCompletionRequestMessage](#schema-chat-completion-request-message) (`#/components/schemas/ChatCompletionRequestMessage`)

    **示例**

    ```json
    [
      {
        "content": "You are a helpful assistant",
        "role": "system"
      },
      {
        "content": "Hi",
        "role": "user"
      }
    ]
    ```

  - **`model`** (必填)

    使用的模型的 ID。请使用 `deepseek-flash` 或 `deepseek-v4-pro`。

    **示例**

    ```json
    "deepseek-flash"
    ```

  - **`thinking`** (可选)

    控制思考模式与非思考模式的转换。省略 `thinking` 或传 `null` 时，模式由 `reasoning_effort` 决定；如果 `reasoning_effort` 也未提供，则默认开启思考模式。提供此对象时，`type` 必填，其模式设置优先于 `reasoning_effort`。

    - **字段**

      - **`type`** (必填)

        如果设为 `enabled`，则使用思考模式。如果设为 `disabled`，则使用非思考模式

  - **`reasoning_effort`** (可选)

    控制思考模式开关与思考强度。`none` 关闭思考模式；`low` / `high` / `max` 开启思考模式。默认强度为 `high`。出于兼容考虑，`minimal` 映射为 `low`，`medium` / `xhigh` 映射为 `high`。

  - **`max_tokens`** (可选)

    限制一次请求中模型生成 completion 的最大 token 数。取值范围为 1 到 384K（393216）。未设置时，非思考模式默认 8K，思考模式默认 64K（`reasoning_effort` 为 `max` 时为 128K）。输入 token 和输出 token 的总长度受模型的上下文长度的限制。详见[模型 & 价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing.md)。

    **示例**

    ```json
    4096
    ```

  - **`response_format`** (可选)

    一个 object，指定模型必须输出的格式。省略或传 `null` 时使用普通文本；提供此对象时，`type` 必填。

    设置为 { "type": "json\_object" } 以启用 JSON 模式，该模式保证模型生成的消息是有效的 JSON。

    **注意:** 使用 JSON 模式时，你还必须通过系统或用户消息指示模型生成 JSON。如果模型的输出无法被识别为 JSON，API 会将其中的非 JSON 内容替换为空格（`U+0020`），因此返回的消息内容可能仅包含空格（看起来为空，此时 finish\_reason 仍可能是 stop）。此外，如果 finish\_reason="length"，这表示生成超过了 max\_tokens 或对话超过了最大上下文长度，消息内容可能会被部分截断。

    - **字段**

      - **`type`** (必填)

        必须是 `text` 或 `json_object`。

        **示例**

        ```json
        "text"
        ```

  - **`stream`** (可选)

    如果设置为 `true`，将会以 SSE（server-sent events）的形式以流式发送消息增量。消息流以 `data: [DONE]` 结尾。

  - **`temperature`** (可选)

    采样温度，介于 0 和 2 之间。更高的值，如 0.8，会使输出更随机，而更低的值，如 0.2，会使其更加集中和确定。 我们通常建议可以更改这个值或者更改 `top_p`，但不建议同时对两者进行修改。思考模式下不生效。

    **示例**

    ```json
    1
    ```

  - **`top_p`** (可选)

    作为调节采样温度的替代方案，模型会考虑前 `top_p` 概率的 token 的结果。所以 0.1 就意味着只有包括在最高 10% 概率中的 token 会被考虑。取值必须大于 0 且不超过 1。我们通常建议修改这个值或者更改 `temperature`，但不建议同时对两者进行修改。实际生效值取决于模型和模式：

    - `deepseek-flash`：思考模式下默认值为 1.0，低于 0.95 的取值会按 0.95 处理；非思考模式下恒为 1.0，传入的值会被忽略。

    - `deepseek-v4-pro`：思考模式下，启用工具调用时恒为 0.95，否则恒为 1.0，传入的值会被忽略。即使提供了 `tools`，将 `tool_choice` 设为 `none` 也会关闭工具调用。非思考模式下使用传入的值，默认值为 1.0。

    **示例**

    ```json
    1
    ```
