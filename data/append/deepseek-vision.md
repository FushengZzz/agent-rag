# 图像理解

`deepseek-flash` 模型支持在文本之外输入图片，你可以让模型描述图片、识别截图中的文字、分析图表等。旧模型名 `deepseek-v4-flash-vision-exp` 仍可调用，但该模型已下线，其请求同样由最新的 Flash 模型承接。

支持的图片格式：**JPEG、PNG、GIF、WebP**。格式由文件实际内容判断，而非文件名或声明的 MIME 类型。

***

## 何时使用 Files API

内联图片（base64 或 `file_data`）会计入 **48 MiB** 的请求体大小限制。以下情况建议使用 [Files API](https://api-docs.deepseek.com/zh-cn/guides/files_api.md)：

- 单个请求会超过请求体大小限制。
- 图片超过 32 MiB（只有通过 Files API 才能使用）。
- 你在多个请求中引用同一张图片，希望避免每次重复上传。

***

<a id="token-usage"></a>

## 限制

- **支持的格式**：JPEG、PNG、GIF、WebP

- **外部 URL 长度**：8192 个字符

- **请求体大小**：48 MiB

- **单张图片文件大小上限（base64 / 外部 URL）**：32 MiB

- **单张图片文件大小上限（Files API `file_id`）**：64 MiB

- **单个请求最大图片数**：600

- **单个请求图片总大小**：不含 `file_id` 图片最多 64 MiB；包含 `file_id` 图片最高 200 MiB

- **图片最大尺寸**：单边最长 8192 像素；单个请求包含 15 张及以上图片时，降为单边最长 4096 像素

Files API 上传文件的存储与上传配额见 [Files API：限制](https://api-docs.deepseek.com/zh-cn/guides/files_api.md#limits)。

***

## 使用限制

- 图片可以出现在 `user`、`system` 和 `tool` 消息中。`assistant` 消息携带图片会返回 `400` 错误。

开启 [模型内容安全](https://api-docs.deepseek.com/zh-cn/guides/safety.md) 后，送入模型的图片会经过审核。图片未通过审核时，响应以拒答结束，并指出是哪些图片，见 [处理拒答](https://api-docs.deepseek.com/zh-cn/guides/safety.md#handling-refusals)。

***
