# 构建 Chatbot

DeepSeek API 提供与 DeepSeek 网页端和 App 一致的对话能力：联网搜索、深度思考搜索、文件输入、阅读链接，以及基础的模型内容安全风控。你可以用它们构建自己的 Chatbot。

搜索和阅读链接都由服务端完成。客户端只需要展示返回的内容块，并在下一轮把它们原样回传。

***

## 功能对照

- **联网搜索**：介绍：非思考模式下，打开 `deepseek_web_search` 工具后，模型可根据提问自动发起网页或图片搜索并附引用作答；指南：[联网搜索](https://api-docs.deepseek.com/zh-cn/guides/web_tools.md#web-search)

- **深度思考搜索**：介绍：思考模式下，打开 `deepseek_web_search` 工具后，模型可在多步推理中自主联网搜索与阅读链接；指南：[深度思考搜索](https://api-docs.deepseek.com/zh-cn/guides/web_tools.md#search-while-thinking)

- **文件输入**：介绍：支持上传 PDF、Word、PowerPoint、图片等格式的文件，完成纯文本提取或图文混排解析后，拼入对话上下文供模型作答；指南：[文件解析](https://api-docs.deepseek.com/zh-cn/guides/document_parsing.md)

- **阅读链接**：介绍：打开 `deepseek_read_url` 工具后，模型可自动识别用户消息中的链接，抓取网页内容并结合上下文作答；指南：[阅读链接](https://api-docs.deepseek.com/zh-cn/guides/web_tools.md#read-links)

- **模型内容安全**：介绍：开启安全校验参数后，我们将提供基础风控，审核模型输入输出，命中风险时返回拒答标识。如您对外提供服务，请开启该参数，并承担内容安全审核、大模型登记、AI 标识等义务；指南：[模型内容安全](https://api-docs.deepseek.com/zh-cn/guides/safety.md)

- **用户元信息标记**：介绍：把当前日期、用户所在地、语言等信息告诉模型，让回答更贴合用户所处的环境；指南：[用户元信息标记](https://api-docs.deepseek.com/zh-cn/guides/latest_reminder.md)

- **会话标题**：介绍：回答结束时，根据对话内容生成一个简短的会话标题；指南：[会话标题](https://api-docs.deepseek.com/zh-cn/guides/conversation_title.md)

- **朗读回答**：介绍：把模型的回答合成为语音播放；指南：[语音合成](https://api-docs.deepseek.com/zh-cn/guides/tts.md)

- **语音输入**：介绍：把用户的语音识别为文字，作为消息发送；指南：[语音识别](https://api-docs.deepseek.com/zh-cn/guides/asr.md)

***

<a id="demo"></a>

## 合规要求

- 开启安全校验参数后，我们将提供基础风控，审核模型输入输出，命中风险时返回拒答标识。如您对外提供服务，请开启该参数，并自行履行服务提供者应承担的内容安全审核、大模型登记、AI 标识等义务。
- 请您遵守我们的开放平台服务协议：[DeepSeek 开放平台服务协议](https://cdn.deepseek.com/policies/zh-CN/deepseek-open-platform-terms-of-service.html)。
