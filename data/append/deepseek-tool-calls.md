# Tool Calls

Tool Calls 让模型能够调用外部工具，来增强自身能力。

***

## 非思考模式

### 样例代码

这里以获取用户当前位置的天气信息为例，展示了使用 Tool Calls 的完整 Python 代码。

Tool Calls 的具体 API 格式请参考[对话补全](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion.md)文档。

这个例子的执行流程如下：

1. 用户：询问现在的天气
2. 模型：返回 function `get_weather({location: 'Hangzhou'})`
3. 用户：调用 function `get_weather({location: 'Hangzhou'})`，并传给模型。
4. 模型：返回自然语言，"The current temperature in Hangzhou is 24°C."

注：上述代码中 `get_weather` 函数功能需由用户提供，模型本身不执行具体函数。

***

## 思考模式

从 DeepSeek-V3.2 开始，API 支持了思考模式下的工具调用能力，详见[思考模式](https://api-docs.deepseek.com/zh-cn/guides/thinking_mode.md#tool-calls)。

***

## 在对话中间插入工具调用

在部分 Agent 场景中，客户端需要把并非由模型生成的工具调用及其结果，动态插入到对话历史的中间。各 API 格式对此的支持情况不同：

- [Anthropic API](https://api-docs.deepseek.com/zh-cn/guides/anthropic_api.md)（`/messages`）与 [Responses API](https://api-docs.deepseek.com/zh-cn/guides/responses_api.md) 支持在对话中间插入工具调用消息，也支持在对话中间插入 `system` 消息；
- Chat Completion 接口不支持在对话中间插入工具调用，但支持在对话中间插入 `system` 消息；如需插入工具调用，请改用 Anthropic API 或 Responses API。

***
