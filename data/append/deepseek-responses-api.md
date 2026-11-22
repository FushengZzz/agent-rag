# 使用 Responses API

为了满足大家对 Codex 的需求，我们的 API 新增了对 Responses API 格式的支持，其 `base_url` 为 `https://api.deepseek.com`。

通过简单的配置，即可在 Codex 中使用 DeepSeek 模型。

## 通过 Responses API 调用 DeepSeek 模型

```python
# Please install OpenAI SDK first: `pip3 install openai`
from openai import OpenAI

client = OpenAI(api_key="<your DeepSeek API Key>", base_url="https://api.deepseek.com")

response = client.responses.create(
    model="deepseek-flash",
    instructions="You are a helpful assistant.",
    input="Hi, how are you?",
)

print(response.output_text)
```

<a id="streaming"></a>
