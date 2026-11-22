# 文件解析

让模型基于你的文件回答问题，与 DeepSeek 网页端上传文件一致。分两步：

1. 把 PDF、Word、PowerPoint、图片等文件上传到 Files API，上传时指定解析方式。
2. 在对话请求中引用返回的 `file_id`。

文件在上传时完成解析，解析成功后才返回 `file_id`。

***

<a id="purposes"></a>

## 选择解析方式

两种方式的区别在于，模型能不能看到文档里的图：

| `purpose`                 | 模型得到的内容                                   | 适合的文档                             |
| ------------------------- | ----------------------------------------- | --------------------------------- |
| `text_recognition`        | 只有文字。文档里的图表、照片、示意图会被丢弃                    | 以文字为主的文档，例如合同、论文、扫描的文字材料          |
| `rich_layout_recognition` | 文字，加上文档里的图：图表、照片、示意图会被裁出来，按原来的位置和文字一起交给模型 | 需要结合图来理解的文档，例如带图表的报告、幻灯片、带示意图的说明书 |

例如，一份财报里有一张营收趋势图，用户问“这张图说明了什么”：

- 用 `text_recognition` 解析，模型只读到正文文字，看不到这张图，只能根据正文作答。
- 用 `rich_layout_recognition` 解析，模型能看到这张图，可以结合正文回答。

文档里的图是在解析时自动识别并裁出的，不保证每张图都能被识别出来。没有被裁出的图，模型仍然看不到。

`rich_layout_recognition` 裁出的图会占用输入 Token，并计入每个请求的图片数量上限。不需要模型看图时，用 `text_recognition` 即可。

***

## 第一步：上传并解析文档

通过 `POST /files` 上传，也可以使用 [Anthropic 兼容接口](https://api-docs.deepseek.com/zh-cn/guides/files_api.md#anthropic-compatible-files-api)。**`purpose` 字段必须放在 `file` 字段之前**。OpenAI Python SDK 会先发送表单字段、再发送文件，无需额外处理。

```bash
curl https://api.deepseek.com/files \
  -H "Authorization: Bearer <DeepSeek API Key>" \
  -F purpose="text_recognition" \
  -F file="@report.pdf"
```

```json
{
  "id": "file-api-xxxxxxxxxxxxxxxx",
  "object": "file",
  "bytes": 1048576,
  "created_at": 1762790000,
  "filename": "report.pdf",
  "purpose": "text_recognition"
}
```

- 解析完成后才返回响应，解析期间不发送任何数据。请把客户端以及中间代理的超时时间设为上传时间加解析时间。
- 客户端中途断开时，解析仍会执行到结束；解析成功的文件照常保存并计费，之后可以在 `GET /files` 中看到。
- 上传失败的文件不会保存，也不计费。
- 上传的原始文件和解析结果都不支持下载。

***

<a id="document-qa"></a>
