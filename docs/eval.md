# 评测基线（10 题）

- **用法**：before = `index_v1`（只入库 data/raw，7 块）；after = `index_v2`（raw + append 29 篇，实测 175 块）。索引与 chunks 成对版本化（index_v1.npz↔chunks_v1.jsonl、index_v2.npz↔chunks_v2.jsonl），评测用 `--index` 指定，绝不读全局缓存。
- **判定口径（L1）**：Hit@1 = top-1 块所属文件 == 预期 source；Recall@5 = top-5 内正确 source 的块含 key。
- **判定口径（L2）**：答案命中 = `keys_all` 全含 / `keys` 任一，匹配前两侧归一化（去 `**`、去空白）；**虚构引用 = 答案中出现的 .md 文件名不在本轮检索 sources 里**（措辞与 key 不同 ≠ 幻觉；纯 `[数字]` 脚注无法对名，只记 cited 不记虚构）。
- **答案可核对性**：所有预期答案均已核对自语料原文（抓取 2026-11-21）。无开放题。
- **Q7–Q10 预期**：before 不命中（语料不在库）；after 应命中——实测 Q10 ✓，Q7/Q9 正确块进了 top-5 但 top-1 被相近内容挤掉，Q8 未召回（见结论）。

| 编号 | 问题 | 预期答案 | 预期命中 source | before top-1 | after top-1 |
| --- | --- | --- | --- | --- | --- |
| Q1 | RAG 切分的常见起点是多大的块？重叠比例设多少？ | 300 到 800 字，重叠 10% 到 15% | data/raw/rag-faq.md | rag-faq.md#0 ✓ | rag-faq.md#0 ✓ |
| Q2 | 检索不准时加 rerank，标准做法是先向量召回多少条、再精排取多少条？ | 先向量召回 20 条，再用交叉编码器精排取 5 条 | data/raw/rag-faq.md | rag-faq.md#1 ✓ | rag-faq.md#1 ✓ |
| Q3 | 按文档说法，绝大多数"召回不准"其实是什么问题？ | 切分问题，不是模型问题 | data/raw/rag-faq.md | rag-faq.md#1 ✓ | rag-faq.md#1 ✓ |
| Q4 | 建评测集时，应该从真实文档里人工写多少个问题？ | 30 到 50 个 | data/raw/rag-faq.md | rag-faq.md#2 ✓ | rag-faq.md#2 ✓ |
| Q5 | Agent 的长期记忆需要哪四个环节？ | 抽取、去重、存储、召回 | data/raw/agent-patterns.md | agent-patterns.md#2 ✓ | agent-patterns.md#2 ✓ |
| Q6 | 防止 Agent 绕圈，文档给出了哪两类机制？ | ①记录已调用的工具和参数组合，相同调用第二次直接拦截；②设置最大步数上限，超限强制收尾 | data/raw/agent-patterns.md | agent-patterns.md#0 ✓ | agent-patterns.md#0 ✓ |
| Q7 | DeepSeek 官方 pricing 页列出的两个模型分别是什么？ | deepseek-flash 和 deepseek-v4-pro | data/append/deepseek-pricing.md | agent-patterns.md#0 ✗ | news261113.md#5 ✗（正确块在 top-5，被 news 挤掉；题干已加"pricing 页"限定，待重测） |
| Q8 | sentence-transformers 官方 README 的快速上手示例加载的是哪个模型？ | sentence-transformers/all-MiniLM-L6-v2 | data/append/sentence-transformers.md | rag-faq.md#1 ✗ | create-chat-completion.md#4 ✗（真 miss：中文 query → 英文文档，跨语言召回弱） |
| Q9 | DeepSeek Chat Completions 的 temperature 参数取值范围是多少？思考模式下生效吗？ | 介于 0 和 2 之间；思考模式下不生效 | data/append/deepseek-api-create-chat-completion.md | rag-faq.md#2 ✗ | anthropic-api.md#4 ✗（正确块在 top-5） |
| Q10 | FastAPI 的 web 部分和数据部分分别基于哪个库？ | web 部分基于 Starlette，数据部分基于 Pydantic | data/append/fastapi.md | agent-patterns.md#0 ✗ | fastapi.md#0 ✓ |

## 结论（2026-11-22，L1 对照实验 + L2 人工复核）

语料从 7 块扩到 175 块（25 倍），对照组 Q1–Q6 的 Hit@1 与 Recall@5 均为 6/6，无退化；Q1–Q6 的 top-1 分数在两套索引下完全一致（0.5440–0.7553，小数点后 6 位相同）——这是预期行为：单块的向量和相似度不依赖语料里还有多少块，真正的风险是干扰项挤进前排。

- **最小余量 0.035**（Q6：正确答案 0.5440 vs 最强干扰 0.5087）：语料再翻倍，Q6 大概率被挤掉。这就是 rerank 的动机——实测推出来的，不是理论推演。
- **v2 组可检索性 Hit@1 1/4、Recall@5 3/4**：Q10 ✓；Q7/Q9 的正确块在 top-5 内但 top-1 被相近内容挤掉（news261113 也提到 deepseek-flash、anthropic-api 也有 temperature 说明）；**Q8 是检索层的真 miss**（top-5 内没有任何 sentence-transformers.md 的块）——中文 query 检索英文文档，bge-small-zh 跨语言召回弱，正是语料清洗时"英文 ≤20%"这条约束的实证。**注意 Q8 在 L2 两次都是 ✓，这不能证明检索成功**：all-MiniLM-L6-v2 是著名模型名，模型可能凭参数知识直接作答（假阳性）。判别方法：L2 结果行补记 `sources` 字段重跑，看 Q8 的 sources 是否含 sentence-transformers.md；不含即坐实。这也坐实了"L1 才是 before/after 主指标"的设计理由。W4 做 rerank 时：Q7/Q9 当"挤掉"用例，Q8 当"跨语言"用例。
- **L2 的"虚构引用 4/20"是误报**：4 条全是措辞差异或语料命名冲突（Q3 回答带加粗标记、Q5 省了"和"、Q9 换说法、Q7 撞上历史公告），逐条对照引用文件都能找到原文，无一条真幻觉。判定逻辑已修正，待重跑。
- **语料命名冲突**：news251201（2025-12 公告）用 DeepSeek-V3.2 / V3.2-Speciale，pricing（当前）用 deepseek-flash / deepseek-v4-pro，以 pricing 页为准；Q7 题干已加限定，记录见 docs/corpus.md。

## 语料清单（data/append，共 29 篇）

- **DeepSeek 官方文档 27 篇**：pricing（模型 & 价格）、api/create-chat-completion、api/create-completion、api/get-user-balance、guides/thinking-mode、guides/tool-calls、guides/kv-cache、guides/vision、guides/anthropic-api、guides/json-mode、guides/chat-prefix-completion、guides/fim-completion、guides/web-tools、guides/responses-api、guides/search、guides/files-api、guides/build-a-chatbot、guides/document-parsing、guides/safety、guides/asr、guides/tts、guides/conversation-title、quick_start/error-codes、quick_start/rate-limit、quick_start/token-usage、updates、news251201、news261113
- **开源项目 README 2 篇**：fastapi、sentence-transformers（核心节）
- **体量**：约 5.2 万字符（含 raw），实测 **175 块**（index_v2 vectors (175, 512)），落在 100–200 目标区间；已按切分约束清洗（删长代码/超长表格转列表/段落按句切分），来源与删除记录见 docs/corpus.md。原始抓取件 46 篇在 data/append-excluded/ 可对照。

## 实测记录（原始输出）

(.venv) PS D:\agent-rag> python.exe -m eval.run_eval --layer l1 --index data/index_v1.npz --out eval/result_v1.json

| group | 题数  | Hit@1      | Recall@5   | 说明               |
| ----- | --- | ---------- | ---------- | ---------------- |
| v1    | 6   | 6/6 (100%) | 6/6 (100%) | 对照实验组（原始 2 篇）    |
| v2    | 4   | 0/4 (0%)   | 0/4 (0%)   | 新增语料可检索性，不计入提升幅度 |

### 明细（before）

| id  | group | top1                | hit1 | recall | match_key      |
| --- | ----- | ------------------- | ---- | ------ | -------------- |
| Q1  | v1    | rag-faq.md#0        | ✓    | ✓      | 300 到 800      |
| Q2  | v1    | rag-faq.md#1        | ✓    | ✓      | 召回 20 条        |
| Q3  | v1    | rag-faq.md#1        | ✓    | ✓      | 切分问题，不是模型问题    |
| Q4  | v1    | rag-faq.md#2        | ✓    | ✓      | 30 到 50        |
| Q5  | v1    | agent-patterns.md#2 | ✓    | ✓      | 抽取、去重、存储和召回    |
| Q6  | v1    | agent-patterns.md#0 | ✓    | ✓      | 记录已调用过的工具和参数组合 |
| Q7  | v2    | agent-patterns.md#0 | ✗    | ✗      | -              |
| Q8  | v2    | rag-faq.md#1        | ✗    | ✗      | -              |
| Q9  | v2    | rag-faq.md#2        | ✗    | ✗      | -              |
| Q10 | v2    | agent-patterns.md#0 | ✗    | ✗      | -              |

(.venv) PS D:\agent-rag> python.exe -m eval.run_eval --layer l1 --index data/index_v2.npz --out eval/result_v2.json

| group | 题数  | Hit@1      | Recall@5   | 说明               |
| ----- | --- | ---------- | ---------- | ---------------- |
| v1    | 6   | 6/6 (100%) | 6/6 (100%) | 对照实验组（原始 2 篇）    |
| v2    | 4   | 1/4 (25%)  | 3/4 (75%)  | 新增语料可检索性，不计入提升幅度 |

### 明细（after，Q7 题干修改后需重跑）

| id  | group | top1                                     | hit1 | recall | match_key      |
| --- | ----- | ---------------------------------------- | ---- | ------ | -------------- |
| Q1  | v1    | rag-faq.md#0                             | ✓    | ✓      | 300 到 800      |
| Q2  | v1    | rag-faq.md#1                             | ✓    | ✓      | 召回 20 条        |
| Q3  | v1    | rag-faq.md#1                             | ✓    | ✓      | 切分问题，不是模型问题    |
| Q4  | v1    | rag-faq.md#2                             | ✓    | ✓      | 30 到 50        |
| Q5  | v1    | agent-patterns.md#2                      | ✓    | ✓      | 抽取、去重、存储和召回    |
| Q6  | v1    | agent-patterns.md#0                      | ✓    | ✓      | 记录已调用过的工具和参数组合 |
| Q7  | v2    | deepseek-news261113.md#5                 | ✗    | ✓      | deepseek-flash |
| Q8  | v2    | deepseek-api-create-chat-completion.md#4 | ✗    | ✗      | -              |
| Q9  | v2    | deepseek-anthropic-api.md#4              | ✗    | ✓      | 介于 0 和 2       |
| Q10 | v2    | fastapi.md#0                             | ✓    | ✓      | Starlette      |

(.venv) PS D:\agent-rag> $env:AGENT_INDEX = "data/index_v2.npz"; python -m eval.run_eval --layer l2 --repeat 2 --out eval/result_l2.json

| group | 题数  | 答案命中        | 带引用          | 虚构引用 | 平均步数 |
| ----- | --- | ----------- | ------------ | ---- | ---- |
| v1    | 12  | 10/12 (83%) | 12/12 (100%) | 2/12 | 3.7  |
| v2    | 8   | 6/8 (75%)   | 8/8 (100%)   | 2/8  | 3.4  |

### L2 明细（旧判定，4 条"虚构引用"经人工复核均为误报，判定修正后重跑）

| id  | 答案命中 | 带引用 | 虚构引用 | 步数  |
| --- | ---- | --- | ---- | --- |
| Q3  | ✗    | ✓   | ⚠    | 4   |
| Q5  | ✗    | ✓   | ⚠    | 3   |
| Q7  | ✗    | ✓   | ⚠    | 3   |
| Q9  | ✗    | ✓   | ⚠    | 4   |

（其余 16 行全部 ✓✓-，完整原始 json 在 eval/result_l2.json）
