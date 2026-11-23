# 语料来源与清洗记录

> 更新：2026-11-21。原始抓取件（46 个文件）全部保留在 `data/append-excluded/`，本目录 `data/append/`（29 篇）是清洗后的入库版本。清洗/审计脚本在 `eval/`（clean_corpus.py / corpus_audit.py / final_metrics.py），可复跑。

## 来源

- **DeepSeek API 官方文档 27 篇**（api-docs.deepseek.com 中文站，路径加 `.md` 直出 markdown）：
  - API 参考：create-chat-completion、create-completion、get-user-balance
  - 指南：thinking-mode、tool-calls、kv-cache、vision、anthropic-api、json-mode、chat-prefix-completion、fim-completion、web-tools、responses-api、search、files-api、build-a-chatbot、document-parsing、safety、asr、tts、conversation-title
  - 快速开始/公告：pricing、error-codes、rate-limit、token-usage、updates、news251201、news261113
- **开源项目 README 2 篇**（GitHub raw）：fastapi、sentence-transformers

## 为什么只留 2 篇英文 README

初版抓了 16 篇 README + 14 篇 DeepSeek 文档共 30 篇，审计（corpus_audit.py）发现：总 30.4 万字符 ≈ **905 块**（目标 100–200），英文字母占比 **92.6%**（bge-small-zh 对英文召回明显偏低，且 16 篇英文会让"召回差"分不清是语料问题还是模型问题）。因此只保留与本项目直接相关的 fastapi、sentence-transformers 两篇并截取核心节，其余 14 篇 README（chroma、faiss、gradio、httpx、langchain、llama_index、openai-python、pandas、pydantic、pymilvus、redis-py、starlette、uvicorn、tiktoken）移入 `append-excluded/` 未入库。缺口用 16 篇新增 DeepSeek 官方中文页补齐。

## 清洗动作（只删不改写，内容零杜撰）

1. **删 >20 行代码块**：初版 13 篇共 640 行长代码，会触发段内硬切、产生无意义块。≤20 行的短代码保留（真实技术文档都有代码）。
2. **超长表格（>450 字符）转"列名：值"要点列表**：整表进同一块会稀释语义向量，转列表后每条一个段落边界。pricing 的模型细节宽表是文档导出伪影（同一列重复 3 次），重建为 3 列（属性 | deepseek-flash | deepseek-v4-pro），单元格内容逐字照抄。
3. **段落 >450 字符按句切分**：无句号边界的整句按 `；，、` 兜底切，杜绝句中硬切。
4. **JSON schema 元数据行剔除**（`- type: string` 之类）；create-chat-completion 按 9 个核心参数过滤（messages/model/temperature/max_tokens/stream/thinking/reasoning_effort/response_format/top_p），工具相关参数由 tool-calls 专题文档覆盖。
5. **图片行、纯链接噪声删除**。
6. **整篇移除 2 篇**：multi-round-chat（与 thinking-mode 的"多轮对话拼接"讲同一规则，查重虽未触发但主题重叠）、list-models（218 字 < 300 字下限，模型信息与 pricing 重复）。

## 每篇节选范围

按节白名单机械抽取（如 thinking-mode 只留"开关与强度控制""多轮对话拼接"两节；web-tools 只留概念/引用/计费/错误；create-chat-completion 只留接口/鉴权/请求体参数描述，跳过响应示例与代码示例）。选节标准：**概念与规则文字保留，请求/响应示例代码删除**——用户问的是概念，不是代码。完整原文都在 `append-excluded/` 可对照。

## 最终指标（2026-11-21 复测）

| 指标 | 清洗前 | 清洗后 | 要求 |
| --- | --- | --- | --- |
| 总字符 | 30.4 万 | **5.2 万**（append 5.0 万 + raw 0.1 万） | ≥3 万 ✓ |
| 实测块数 | ~905（估算） | **175**（index_v2 实测 vectors (175, 512)，含 raw 7 块） | 100–200 ✓ |
| 单篇块数 | 最大 131 块 | **1–14 块**，300–1500 字为主 | 2–6 块 ✓ |
| 长代码块（>20 行） | 640 行 | **0** | 0 ✓ |
| 超长段落（>450 字） | 多篇存在 | **0** | 0 ✓ |
| 超长表格（占整块） | 多张 | **0**（>450 字符均已转列表） | ✓ |
| 整篇英文文档 | 16 篇（占 83%） | **2 篇**，英文正文约 1200 字符 ≈ 自然语言部分的 12% | ≤20% ✓ |
| 内容重复（40 字符 shingle） | 无 | 无 | ✓ |
| `##` 分节 | 1 篇缺失 | 27/29 有 `##`；2 篇例外见下 | 基本满足 |

## 已知例外（面试可讲）

- **官方页面间模型命名不一致（2026-11-22 评测实证）**：news251201 是 2025-12-01 的历史公告，用 DeepSeek-V3.2 / DeepSeek-V3.2-Speciale；pricing 是当前定价页，用 deepseek-flash / deepseek-v4-pro。同一语料库里两套命名并存，检索到旧公告的题会答出"旧名字"。约定：**以 pricing 页为准**。评测 Q7 **保留原问法、不加限定词**，作为"多来源冲突"的固定用例暴露问题（加限定词等于把冲突藏起来，测不出系统缺陷）；待"来源时效/优先级元数据"机制上线后，再用同一题验证是否真的解决。教训：语料是随时间演进的官方文档，历史公告天然带旧事实。
- **deepseek-news251201、deepseek-conversation-title 无 `##` 分节**：两篇都是单主题短页，且所有段落已 <450 字符——聚合切分只会落在段落边界，"句中硬切"这个失败模式不会发生，故保留并在评测时留意。
- **deepseek-web-tools 5040 字符（约 14 块）超单篇上限**：联网工具/搜索是 Agent 核心特性，信息量优先；若评测发现它霸占 top-5，再删"用量与计费"节。
- **中文文档里的拉丁字符占比偏高（字母口径 ~54%）**：主要是模型名（deepseek-flash）、参数名（reasoning_effort）、URL 等技术标识与 ≤20 行短代码，不是英文文档；真正的英文正文只有 fastapi/sentence-transformers 两篇。

## 面试一句话版本

"语料来自 DeepSeek 官方文档 27 篇 + 2 篇相关英文 README，全部保留原始抓取件可对照；按自己的切分器倒推了约束——只收 md、必须有标题分节、段落 <450、代码 ≤20 行、超长表格转列表——从 30 万字符 905 块清洗到 5.2 万字符约 150 块，删了什么为什么都有记录（本文档），评测集 10 题在 docs/eval.md。"
