# FIM 补全 API（Beta）
## 接口

```http
POST /completions
```

operationId: `createCompletion`

### 服务地址

- `https://api.deepseek.com/beta`

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

- 引用: [CreateCompletionRequest](#schema-create-completion-request) (`#/components/schemas/CreateCompletionRequest`)

### schema-create-completion-request

**CreateCompletionRequest** — `#/components/schemas/CreateCompletionRequest`

- **字段**

  - **`model`** (必填)

    模型的 ID。请使用 `deepseek-flash` 或 `deepseek-v4-pro`。

  - **`prompt`** (必填)

    用于生成完成内容的提示

  - **`echo`** (可选)

    在输出中，把 prompt 的内容也一并返回。不能与 `suffix` 或 `logprobs` 一起使用。

  - **`logprobs`** (可选)

    指定输出中包含 logprobs 最可能输出 token 的对数概率，包含采样的 token。例如，如果 logprobs 是 20，API 将返回一个包含 20 个最可能的 token 的列表。API 将始终返回采样 token 的对数概率，因此响应中可能会有最多 logprobs+1 个元素。

    logprobs 的最大值是 20。

  - **`max_tokens`** (可选)

    最大生成 token 数量。

    **示例**

    ```json
    1024
    ```

  - **`stop`** (可选)

    一个 string 或最多包含 16 个 string 的 list，在遇到这些词时，API 将停止生成更多的 token。每个 string 不能为空，且不能超过 512 字节（UTF-8 编码）。

    - **oneOf**

      - oneOf 1

        **示例**

        ```json
        null
        ```

      - oneOf 2

        - **数组元素**

          **示例**

          ```json
          "[\"\\n\"]"
          ```

  - **`stream`** (可选)

    如果设置为 `true`，将会以 SSE（server-sent events）的形式以流式发送消息增量。消息流以 `data: [DONE]` 结尾。

  - **`stream_options`** (可选)

    - 引用: [ChatCompletionStreamOptions](#schema-chat-completion-stream-options) (`#/components/schemas/ChatCompletionStreamOptions`)

  - **`suffix`** (可选)

    补全内容之后的后缀。

    **示例**

    ```json
    null
    ```

  - **`temperature`** (可选)

    采样温度，介于 0 和 2 之间。更高的值，如 0.8，会使输出更随机，而更低的值，如 0.2，会使其更加集中和确定。 我们通常建议可以更改这个值或者更改 `top_p`，但不建议同时对两者进行修改。

    **示例**

    ```json
    1
    ```

  - **`top_p`** (可选)

    作为调节采样温度的替代方案，模型会考虑前 `top_p` 概率的 token 的结果。所以 0.1 就意味着只有包括在最高 10% 概率中的 token 会被考虑。 取值必须大于 0 且不超过 1。我们通常建议修改这个值或者更改 `temperature`，但不建议同时对两者进行修改。

    **示例**

    ```json
    1
    ```

  - **`frequency_penalty`** (可选)

    该参数已不再支持。传入该参数将不会产生任何效果。

  - **`presence_penalty`** (可选)

    该参数已不再支持。传入该参数将不会产生任何效果。
