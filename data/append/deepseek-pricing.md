# 模型 & 价格

下表所列模型价格以“百万 tokens”为单位。Token 是模型用来表示自然语言文本的最小单位，可以是一个词、一个数字或一个标点符号等。我们将根据模型输入和输出的总 token 数进行计量计费。

***

## 模型细节

- **模型版本**：deepseek-flash(1)：DeepSeek-V4.1-Flash-1017；deepseek-v4-pro：DeepSeek-V4-Pro-0813

- **功能**：deepseek-flash(1)：[Json Output](https://api-docs.deepseek.com/zh-cn/guides/json_mode.md)；deepseek-v4-pro：支持

- **功能**：deepseek-flash(1)：[Tool Calls](https://api-docs.deepseek.com/zh-cn/guides/tool_calls.md)；deepseek-v4-pro：支持

- **功能**：deepseek-flash(1)：[Responses API](https://api-docs.deepseek.com/zh-cn/guides/responses_api.md)；deepseek-v4-pro：支持

- **功能**：deepseek-flash(1)：[Anthropic API](https://api-docs.deepseek.com/zh-cn/guides/anthropic_api.md)；deepseek-v4-pro：支持

- **功能**：deepseek-flash(1)：[对话前缀续写（Beta）](https://api-docs.deepseek.com/zh-cn/guides/chat_prefix_completion.md)；deepseek-v4-pro：支持

- **功能**：deepseek-flash(1)：[FIM 补全（Beta）](https://api-docs.deepseek.com/zh-cn/guides/fim_completion.md)；deepseek-v4-pro：仅非思考模式支持

- **[图像理解](https://api-docs.deepseek.com/zh-cn/guides/vision.md)**：deepseek-flash(1)：支持；deepseek-v4-pro：不支持

- **百万tokens输入 / （缓存命中），空闲时段**：deepseek-flash(1)：0.02元；deepseek-v4-pro：0.15元

- **百万tokens输入 / （缓存命中），高峰时段**：deepseek-flash(1)：0.04元；deepseek-v4-pro：0.30元

- **百万tokens输入 / （缓存未命中），空闲时段**：deepseek-flash(1)：1元；deepseek-v4-pro：4.5元

- **百万tokens输入 / （缓存未命中），高峰时段**：deepseek-flash(1)：2元；deepseek-v4-pro：9.0元

- **百万tokens输出，空闲时段**：deepseek-flash(1)：4元；deepseek-v4-pro：13.5元

- **百万tokens输出，高峰时段**：deepseek-flash(1)：8元；deepseek-v4-pro：27.0元

- **并发限制(3)**：deepseek-flash(1)：2500；deepseek-v4-pro：500

(1) 模型名请使用 `deepseek-flash`。旧模型名 `deepseek-v4-flash`、`deepseek-v4-flash-vision-exp` 仍可调用，但对应模型已下线，请求将由 DeepSeek-V4.1-Flash-1017 模型提供服务，并按 Flash 价格计费。

(2) 空闲时段价格为高峰时段价格的一半。北京时间周一至周五（不含中国法定节假日）9:00 - 12:00、14:00 - 18:00 为高峰时段；其余时段，包括周末及中国法定节假日全天均为空闲时段。

(3) 更多并发限制细节，请参考[限速与隔离](https://api-docs.deepseek.com/zh-cn/quick_start/rate_limit.md)。

***

<a id="网页搜索与抓取价格"></a>

<a id="web-tools-pricing"></a>

## 扣费规则

模型调用费用 = token 消耗量 × 模型单价；Search API 与 Fetch API 按上表价格按次计费。对应的费用将直接从充值余额或赠送余额中进行扣减。
当充值余额与赠送余额同时存在时，优先扣减赠送余额。

产品价格可能发生变动，DeepSeek 保留修改价格的权利。请您依据实际用量按需充值，定期查看此页面以获知最新价格信息。
