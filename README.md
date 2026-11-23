# agent-rag

基于 DeepSeek Function Calling 的文档问答 Agent：本地向量检索（bge-small-zh）+ ReAct 工具循环 + 会话记忆，配套**两层评测**（检索层 L1 / 端到端 L2）和 **before/after 对照实验**。

> 本 README 只写可验证的内容：每个数字都标了出处，复现命令见文末。设计取舍的完整论证在 `docs/decisions.md`，评测口径与结论在 `docs/eval.md`，语料来源与清洗记录在 `docs/corpus.md`。

## 指标总表

| 指标       | 数值                                                                                                    | 出处                                                             |
| -------- | ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| 语料规模     | 31 篇 md（raw 2 + append 29），**175 块**，约 5.2 万字符                                                        | `data/index_v2.npz` vectors (175, 512)；清洗记录 `docs/corpus.md`   |
| 检索延迟     | 单次检索 p50 **≈ 5.5ms**（其中 175×512 全量余弦 **0.05ms**，CPU）                                                  | `eval/measure_latency.py` 可复跑                                  |
| L1 对照实验  | 语料 7 → 175 块（25 倍），对照组 Q1–Q6 Hit@1 / Recall@5 = **6/6 → 6/6，零退化**；且 top-1 分数在两套索引下逐位一致（0.5440–0.7553） | `docs/eval.md` 结果总表 + `eval/result_v1.json` / `result_v2.json` |
| L1 新语料组  | Hit@1 **1/4**，Recall@5 **3/4**（三类失败已归因，见评测一节）                                                         | 同上                                                             |
| L2 端到端   | v1 组 **12/12**、v2 组 **6/8**（唯二失败为语料命名冲突 Q7 两轮）；虚构引用 **0/20**；平均步数 3.50 / 3.62                         | `eval/result_l2.json`                                          |
| 上下文缓存    | 固定前缀（system prompt + 3 个工具 schema）不变，**可缓存前缀约 640 token 恒定命中**；命中率随上下文总长浮动 39%–80%（首轮 39%，多轮升高，历史被压缩后总量变小回落到 53%） | `docs/decisions.md` 缓存条目；各轮原始 `usage` 见 `docs/eval.md` |
| 会话记忆     | 保留最近 3 轮原文（上下文注入恒为 6 条 message）+ 一条 ≤200 字摘要（temperature=0）；压缩失败时保底不丢历史                               | `app/memory.py`（`KEEP_TURNS=3` / `SUMMARY_MAX_CHARS=200`）      |
| Agent 循环 | ReAct 上限 5 步，超限用 `tool_choice="none"` 强制收尾；(工具名, 参数) 集合去重拦截绕圈；工具返回 >2000 字符截断                         | `app/agent.py` / `app/tools/registry.py`                       |

## 架构

两条链路（完整 mermaid 图、数据形态表、失败路径表见 `docs/architecture.md`）：

- **离线**：`data/raw` + `data/append` → `ingest.py`（切分 + 编码 + 落盘 `index_v2.npz` / `chunks_v2.jsonl`）
- **在线**：`POST /ask` → `memory`（取历史/摘要）→ `agent`（ReAct 循环，调 `search_docs` / `calc` / `lookup`）→ deepseek-chat → 答案 + 来源脚注

| 组件        | 选择                                                   | 一句话理由                                            |
| --------- | ---------------------------------------------------- | ------------------------------------------------ |
| embedding | `BAAI/bge-small-zh-v1.5`，本地 CPU，512 维，L2 归一化         | DeepSeek 无 embedding 接口；本地免费离线；单例加载防双实例          |
| 向量检索      | numpy 全量余弦（`vectors @ query`）                        | 175 块余弦实测 0.05ms，引入向量库是过度设计                      |
| 切分        | 段落聚合 ≤450 字符 + `##` 标题强制断块 + <80 字短块合并，**零 overlap** | 边界来自文档结构；overlap 是给"不可靠边界"兜底的                    |
| 生成        | `deepseek-chat` + Function Calling                   | Agent 一轮多次调用，要快与稳                                |
| 服务        | FastAPI，路由用 `def`（内部是阻塞调用，丢线程池而不是堵事件循环）              | `/ask`、`/health`、`/ingest`、`/sessions/{id}` 调试接口 |

## 检索层

- 索引与 chunks **成对版本化**：`chunks_path_for()` 从 `index_v2.npz` 推导 `chunks_v2.jsonl`，行数不一致直接 `raise ValueError`（不用 assert，`python -O` 会吞掉 assert）。
- `search_docs` 返回带来源与相似度的编号列表，模型直接据此标注引用；`AGENT_INDEX` 环境变量切换被测索引。

## Agent 层（ReAct）

- 三个工具：`search_docs`（语义检索，带来源）、`calc`（字符白名单校验，拒绝裸 eval 注入）、`lookup`（按文件名取全文）。
- 兜底四件套：检索 0 结果直说不硬答；工具异常作为消息回传模型可重试；达到步数上限强制收尾并声明"基于已有信息"；重复 (工具, 参数) 第二次直接拦截。
- 每步落轨迹（`steps`），返回 `terminated_by: final / max_steps / error` 三态。
- system prompt 与工具 schema 内容固定，摘要作为**独立的 system 消息放在主 prompt 之后**（而不是拼进 system prompt）——前缀一变缓存就整段失效，这是记忆模块里最值得讲的设计。

## 评测（为什么两层、口径为什么改了三次）

- **L1 检索层**：不调 LLM，秒级可复现，是 before/after 的主指标。**L2 端到端**：每题独立 session（session_id 绝不复用，否则测到的是记忆不是检索），repeat=2。
- 判定口径修了三轮才稳定：整串精确匹配 → 归一化 + `keys_all` 实体全含；"虚构引用"从"没命中 key 且带引用"改为"**引用的 .md 文件名不在本轮检索 sources 里**"。前两版判定会把一个 12/12 的系统报成 10/12，并凭空造出 4 条"幻觉"。
- 对照实验结论：语料扩 25 倍对照组零退化；**风险是余量不是命中率**——Q6 正确答案 0.5440 vs 最强干扰 0.5087，余量仅 0.035。
- v2 组三个失败三种性质：Q7 = 语料命名冲突（历史公告 vs 当前定价页，以 pricing 为准）；Q9 = 同主题竞争（rerank 靶子）；Q8 = 跨语言（中文 query → 英文文档，L1 彻底 miss）。
- **Q8 的 L1✗ / L2✓ 差异**：探针验证 Agent 把中文问题改写成含英文库名的 query 后检索到了目标文件——agentic retrieval 对单次检索的实测补偿。L1 是保守下界，L2 是用户视角，两个都报。

## 已知限制

1. 未做 rerank：最小余量 0.035，语料再翻倍预期会翻车（W4 的第一件事）。
2. 跨语言召回：中文 query 对英文文档 L1 失败，agent 改写可补偿但不可靠（多语言 embedding 是备选）。
3. 语料时效治理未做：历史公告与当前定价页命名冲突，**评测保留原问法以暴露该缺陷**（不加题干限定，避免掩盖问题），待来源时效/优先级元数据机制上线后再用同一题验证。记录见 `docs/corpus.md`。
4. 会话历史只在进程内存，重启丢失（单机 demo 的已知取舍）；`/ask/stream` 只有设计注释未实现；PDF 未接，只收 md/txt。
5. 评测规模有限：10 题 × repeat 2，L2 有随机性，只作趋势参考。

## 快速开始

```bash
# 环境（Windows；系统 Git Bash 的 python 无 pip，必须走 venv，详见 docs/decisions.md）
py -3.12 -m venv .venv
source .venv/Scripts/activate          # 或始终用 .venv/Scripts/python.exe
pip install -r requirements.txt

# .env 需要两行：
#   DEEPSEEK_API_KEY=sk-...
#   HF_ENDPOINT=https://hf-mirror.com   （加速 bge 模型下载）

# 建索引（索引与 chunks 自动成对命名）
python -m app.ingest --index data/index_v1.npz            # before：只入库 data/raw
python -m app.ingest --index data/index_v2.npz --with-append   # after：raw + append

# 起服务（Swagger UI: http://127.0.0.1:8000/docs）
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 评测
python -m eval.run_eval --layer l1 --index data/index_v1.npz --out eval/result_v1.json
python -m eval.run_eval --layer l1 --index data/index_v2.npz --out eval/result_v2.json
AGENT_INDEX=data/index_v2.npz python -m eval.run_eval --layer l2 --repeat 2 --out eval/result_l2.json

# 检索延迟实测
python eval/measure_latency.py
```

## 目录结构

```
app/         # embedding.py / ingest.py / retrieve.py / agent.py / memory.py / llm.py / main.py / tools/
data/raw     # 原始语料（2 篇）
data/append  # 扩充语料（29 篇，已按切分约束清洗）
data/append-excluded/  # 语料原始抓取件归档（46 篇，可对照）
docs/        # architecture / decisions / corpus / eval
eval/        # questions.jsonl / run_eval.py / result_*.json / measure_latency.py
```

## 文档

- `docs/architecture.md` — 架构图、数据形态、状态存放位置、失败路径表
- `docs/decisions.md` — 设计决策记录（为什么不用向量库 / 零 overlap / 按 `##` 断块 / 路由用 def…）
- `docs/corpus.md` — 语料来源、清洗动作与理由（面试问"语料哪来的、怎么清洗的"的答案）
- `docs/eval.md` — 评测终版：结果总表、L1/L2 明细、判定口径的三次修正、结论与 W4 输入
