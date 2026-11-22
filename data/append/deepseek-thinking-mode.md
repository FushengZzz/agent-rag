# 思考模式

DeepSeek 模型支持思考模式：在输出最终回答之前，模型会先输出一段思维链内容，以提升最终答案的准确性。

## 思考模式开关与思考强度控制

- **思考模式开关(1)**：控制参数（OpenAI 格式）：`{"thinking": {"type": "enabled/disabled"}}`；控制参数（Anthropic 格式）：`{"thinking": {"type": "enabled/disabled"}}`；控制参数（Responses API 格式）：`{"reasoning": {"effort": "none/low/high/max"}}` / (none 表示关闭思考模式)

- **思考强度控制(2)**：控制参数（OpenAI 格式）：`{"reasoning_effort": "low/high/max"}`；控制参数（Anthropic 格式）：`{"output_config": {"effort": "low/high/max"}}`；控制参数（Responses API 格式）：`{"reasoning": {"effort": "none/low/high/max"}}` / (none 表示关闭思考模式)

(1) 思考模式默认打开，且 effort 默认为 `high` /&#x20;
(2) 用户设置的 effort 与模型推理 effort 映射表如下：

| 请求传入 effort | 实际映射 effort |
| ----------- | ----------- |
| minimal     | low         |
| low         | low         |
| medium      | high        |
| high        | high        |
| xhigh       | high        |
| max         | max         |
| ultra       | max         |

您在 OpenAI SDK 中使用 Chat Completion 设置 `thinking` 参数时，需要将 `thinking` 参数传入 `extra_body` 中：

```python
response = client.chat.completions.create(
  model="deepseek-flash",
  # ...
  reasoning_effort="high",
  extra_body={"thinking": {"type": "enabled"}},
)
```

## 多轮对话拼接

在每一轮对话过程中，模型会输出思维链内容（`reasoning_content`）和最终回答（`content`）。如果请求未携带 `tools` 参数，则在下一轮对话中，之前轮输出的思维链内容不会被拼接到上下文中，如下图所示：

### 样例代码

下面的代码以 Python 语言为例，展示了如何访问思维链和最终回答，以及如何在多轮对话中进行上下文拼接。

**非流式**

**流式**

<a id="tool-calls"></a>
