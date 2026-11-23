# 评测基线（10 题 · 终版）

> 终版更新：2026-11-22。三份原始输出在 `eval/result_v1.json`、`result_v2.json`、`result_l2.json`。

- **用法**：before = `index_v1`（只入库 `data/raw`，7 块）；after = `index_v2`（`data/raw` + `data/append` 29 篇，实测 **175 块**）。索引与 chunks 成对版本化（`index_v1.npz` ↔ `chunks_v1.jsonl`），用 `--index` 指定，绝不读全局缓存。
- **判定口径（L1）**：`Hit@1` = top-1 块所属文件 == 预期 source；`Recall@5` = top-5 内**属于预期 source 的块**含 key（key 命中但文件不对不算）。
- **判定口径（L2）**：答案命中 = `keys_all` 全含 / `keys` 任一，匹配前两侧归一化（去 `**`、去空白）；**虚构引用 = 答案里出现的 .md 文件名不在本轮检索 `sources` 里**（措辞与 key 不同 ≠ 幻觉）。
- **答案可核对性**：所有预期答案均已核对自语料原文（抓取 2026-11-21），无开放题。

## 一、结果总表

| 层 | 索引 | 组 | 题数/轮数 | Hit@1 / 答案命中 | Recall@5 | 虚构引用 |
|---|---|---|---|---|---|---|
| L1 检索 | v1（7 块） | v1 | 6 | **6/6 (100%)** | **6/6 (100%)** | — |
| L1 检索 | v1（7 块） | v2 | 4 | 0/4 (0%) | 0/4 (0%) | — |
| L1 检索 | v2（175 块） | v1 | 6 | **6/6 (100%)** | **6/6 (100%)** | — |
| L1 检索 | v2（175 块） | v2 | 4 | 1/4 (25%) | 3/4 (75%) | — |
| L2 端到端 | v2（175 块） | v1 | 12（×2 轮） | **12/12 (100%)** | — | **0/12** |
| L2 端到端 | v2（175 块） | v2 | 8（×2 轮） | 6/8 (75%) | — | **0/8** |

L2 平均步数 3.5（v1 组）/ 3.6（v2 组），带引用率 100%。

## 二、L1 明细

### before（index_v1，7 块）

| id | group | top1 | hit1 | recall | match_key |
|---|---|---|---|---|---|
| Q1 | v1 | rag-faq.md#0 | ✓ | ✓ | 300+800+10%+15% |
| Q2 | v1 | rag-faq.md#1 | ✓ | ✓ | 召回 20 条 |
| Q3 | v1 | rag-faq.md#1 | ✓ | ✓ | 切分问题 |
| Q4 | v1 | rag-faq.md#2 | ✓ | ✓ | 30 到 50 |
| Q5 | v1 | agent-patterns.md#2 | ✓ | ✓ | 抽取+去重+存储+召回 |
| Q6 | v1 | agent-patterns.md#0 | ✓ | ✓ | 记录已调用过的工具和参数组合 |
| Q7 | v2 | agent-patterns.md#0 | ✗ | ✗ | - |
| Q8 | v2 | rag-faq.md#1 | ✗ | ✗ | - |
| Q9 | v2 | rag-faq.md#2 | ✗ | ✗ | - |
| Q10 | v2 | agent-patterns.md#0 | ✗ | ✗ | - |

### after（index_v2，175 块）

| id | group | top1 | hit1 | recall | match_key |
|---|---|---|---|---|---|
| Q1 | v1 | rag-faq.md#0 | ✓ | ✓ | 300+800+10%+15% |
| Q2 | v1 | rag-faq.md#1 | ✓ | ✓ | 召回 20 条 |
| Q3 | v1 | rag-faq.md#1 | ✓ | ✓ | 切分问题 |
| Q4 | v1 | rag-faq.md#2 | ✓ | ✓ | 30 到 50 |
| Q5 | v1 | agent-patterns.md#2 | ✓ | ✓ | 抽取+去重+存储+召回 |
| Q6 | v1 | agent-patterns.md#0 | ✓ | ✓ | 记录已调用过的工具和参数组合 |
| Q7 | v2 | deepseek-news261113.md#5 | ✗ | ✓ | deepseek-flash+deepseek-v4-pro |
| Q8 | v2 | deepseek-api-create-chat-completion.md#4 | ✗ | ✗ | - |
| Q9 | v2 | deepseek-anthropic-api.md#4 | ✗ | ✓ | 0 和 2 |
| Q10 | v2 | fastapi.md#0 | ✓ | ✓ | Starlette |

## 三、结论

**1. 语料扩 25 倍（7 → 175 块），对照组 Q1–Q6 的检索质量零退化。**

Hit@1 与 Recall@5 均 6/6。且 Q1–Q6 的 top-1 分数在两套索引下**完全一致**（0.5440–0.7553，小数点后 6 位相同）——这是预期行为而非 bug：单块向量及其与 query 的余弦值不依赖语料里还有多少块。真正的风险不是"分数变化"，是"干扰项挤进前排"。

**2. 风险是余量，不是命中率。最小余量只有 0.035。**

Q6 的正确答案 0.5440，最强干扰（`agent-patterns.md#1`）0.5087。Q1 的余量是 0.151（0.6244 vs 0.4734）。也就是说：**在 175 块这个量级下，向量检索还撑得住；再翻一倍，Q6 这类问题就会开始翻车。** 这是 rerank 的实测动机，不是理论推演。

**3. v2 组三类失败，性质完全不同，处理方式也不同。**

| 题 | 现象 | 性质 | 处理 |
|---|---|---|---|
| Q7 | 正确块在 top-5，top-1 被 `news261113` 挤掉 | **语料命名冲突**（见第 4 条） | 语料治理，不是模型问题 |
| Q9 | 正确块在 top-5，top-1 被 `anthropic-api` 挤掉 | **相近内容竞争**（两个页面都讲 temperature） | rerank 的典型用例 |
| Q8 | top-5 内没有任何 `sentence-transformers.md` 的块 | **跨语言召回失败**：中文 query 检索英文文档 | 语料约束（英文 ≤20%）的实证；或换多语言 embedding |

**4. Q7 失败源于语料内部矛盾，必须以 `pricing` 页为准。**

`news251201`（2025-12 公告）用 `DeepSeek-V3.2 / V3.2-Speciale`，`pricing`（当前）用 `deepseek-flash / deepseek-v4-pro`。模型检索到公告就答公告。这不是检索错、也不是生成错，是**语料治理问题**。处理：给来源加时效/优先级元数据，并在评测里显式记录冲突，而不是让模型自己猜。记录见 `docs/corpus.md`。

**5. L2 与 L1 的差异揭示了"单次检索"和"Agent 检索"的真实差距。**

Q8 在 L1（固定中文 query）是**彻底的 miss**，但在 L2 两轮都答对。为排除"参数知识假阳性"，单独探针验证：

```
query 改写为：'sentence-transformers README 快速上手 示例 加载模型'
sources     ：['sentence-transformers.md', 'sentence-transformers.md', 'sentence-transformers.md']
```

**Agent 把中文问题改写成含英文库名的混合 query，真的检索到了目标文件。** 这是 agentic retrieval 相对单次检索的实测补偿，不是模型凭记忆作答。同时它也说明：**L1 是保守下界，L2 才是用户视角的真实表现**，两者必须都报，不能只挑好看的。

**6. 答案层：v1 组 12/12，v2 组 6/8，虚构引用 0/20。**

唯一持续失败的只有 Q7（语料冲突，两轮都答公告版模型名）。`sources` 与答案引用 100% 对得上，没有出现"标了来源但来源不存在"的情况。

## 四、判定口径的三次修正（这段是评测工作里最费时的部分）

| 轮次 | 原判定 | 问题 | 改成 |
|---|---|---|---|
| 1 | key 整串精确匹配 | 答案带 `**` 加粗 → 假阴性（Q3） | 匹配前归一化（去标记/空白） |
| 2 | 同上 | 「抽取、去重、存储**和**召回」vs 模型省略"和" → 假阴性（Q5） | 改用 `keys_all` 实体列举 |
| 3 | 同上 | `300～800` vs `300 到 800` → 假阴性（Q1） | 数字实体全含即命中 |
| — | 虚构引用 = "答案未命中 key 且带引用" | 4 条全误报（措辞差异被当成幻觉） | 虚构引用 = "引用的文件名不在本轮 sources 里" |

**结论：定义"什么算对"比跑分难得多。** 前两版判定会把一个 90% 正确的系统报成 83%，并凭空造出 4 个"幻觉"。

## 五、W4 的输入

| 用例 | 用途 |
|---|---|
| Q6（余量 0.035）、Q9（同主题竞争） | rerank 的收益靶子 |
| Q8（跨语言） | 多语言 embedding 或 query 改写的收益靶子 |
| Q7（语料冲突） | 来源优先级 / 元数据治理的靶子 |

## 六、复现

```bash
# 建两套索引（索引与 chunks 自动成对命名）
python -m app.ingest --index data/index_v1.npz
python -m app.ingest --index data/index_v2.npz --with-append

# L1
python -m eval.run_eval --layer l1 --index data/index_v1.npz --out eval/result_v1.json
python -m eval.run_eval --layer l1 --index data/index_v2.npz --out eval/result_v2.json

# L2（每题独立 session，重复 2 轮）
AGENT_INDEX=data/index_v2.npz python -m eval.run_eval --layer l2 --repeat 2 --out eval/result_l2.json
```

L2 的 `session_id` 格式为 `eval-{题号}-{轮次}`，**绝不复用**：复用会让前几题的答案与摘要进上下文，测到的是记忆而不是检索。
