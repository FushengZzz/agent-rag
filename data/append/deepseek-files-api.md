# Files API

Files API 让你上传文件，之后通过 `file_id` 引用。可以上传两类文件：

- **图片**：JPEG、PNG、GIF、WebP，格式由文件实际内容判断。引用方式见 [图像理解](https://api-docs.deepseek.com/zh-cn/guides/vision.md)。
- **文档**：PDF、Word、PowerPoint、Excel、电子书与纯文本。引用方式见 [文件解析](https://api-docs.deepseek.com/zh-cn/guides/document_parsing.md)。

上传的文件与 `deepseek-flash` 模型配合使用。

***

## 在对话请求中使用已上传的文件

使用 `file` 内容块引用返回的 `file_id`：

```python
response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "这张图片里有什么？"},
                {"type": "file", "file_id": "file-api-xxxxxxxxxxxxxxxx"},
            ],
        },
    ],
)
print(response.choices[0].message.content)
```

文件归属于你的账号：同一账号下的所有 API key 共享文件，且可被任一 API 家族引用。注意：通过 Anthropic 兼容 `/messages` 端点引用文件时需携带 `anthropic-beta: files-api-2025-04-14` 请求头。

与内联（base64）图片不同，通过 `file_id` 引用的文件不受 32 MiB 单图限制，请求中单张最大 64 MiB。

`file` 块也可以通过 `file_data` 以 base64 形式内联携带图片，替代 `file_id`（二者互斥）。使用 `file_data` 时还可设置 `filename`；`filename` 不能与 `file_id` 同时出现。

***

<a id="documents"></a>

## 限制

- **支持的格式**：图片：JPEG、PNG、GIF、WebP。其他文件见上文的 `purpose` 表格

- **单个上传文件大小上限**：图片 64 MiB；PDF、Word、PowerPoint 等文档 100 MiB；纯文本、表格与电子书 32 MiB

- **文件名最大长度**：512 字节

- **单用户最大存储空间**：25 GiB

- **单用户最大存储文件数**：10000

- **文件有效期范围**：1 小时到 30 天，或不传 `expires_after` 永久有效
