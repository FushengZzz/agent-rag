"""检索层 + 端到端评测。

分两层，因为它们的成本和可信度完全不同：

  L1 检索层：不调 LLM，只问"正确内容有没有进 top-k"。
     秒级、可复现、单变量。**before/after 的主指标看这层。**
  L2 端到端：每题独立 session 调 chat()，看答案对不对。
     慢（每题一次完整 Agent 循环）、有随机性。只作为趋势参考，跑 2-3 次取多数。

跑法：
    # 先看现有索引（v1，2 篇）
    .venv/Scripts/python.exe -m eval.run_eval --layer l1 --index data/index_v1.npz

题库在 eval/questions.jsonl，每题长这样：
    {"id": "Q1", "question": "...", "keys": ["300 到 800 字"], "expected_source": "rag-faq.md", "group": "v1"}
  - keys          预期答案里的关键字符串，命中任一即算 Recall@k 成功
  - group         "v1" = 答案在原始 2 篇里（能进对照实验）
                  "v2" = 答案只在新增语料里（只验证可检索，不进对照表）
"""

import argparse
import json
from pathlib import Path
from app.retrieve import load_index, search
import re 
from app.agent import chat

QUESTIONS_PATH = Path("eval/questions.jsonl")

def _norm(s: str) -> str:
    s = (s or "").replace("**", "").replace("*", "")
    return re.sub(r"\s+", "", s)          # 去加粗+去全部空白，'0 和 2'=='0和2'

def _keys_hit(q: dict, text: str) -> tuple[bool, str | None]:
    t = _norm(text)
    if q.get("keys_all"):
        if all(_norm(k) in t for k in q["keys_all"]):
            return True, "+".join(q["keys_all"])
        return False, None
    for k in q.get("keys", []):
        if _norm(k) in t:
            return True, k
    return False, None



def load_questions(path: Path = QUESTIONS_PATH) -> list[dict]:
    """读题库。空行跳过。

    TODO(你): 实现。每行 json.loads，返回 list。
    """
    questions = []
    with open(path,encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            questions.append(json.loads(line))
    return questions


def eval_retrieval(questions: list[dict], index_path: str, top_k: int = 5) -> list[dict]:
    """L1：对每题跑一次检索，判断命中情况。

    对每题返回：
        {"id": "Q1",
         "hit1_file": bool,          # top-1 的 source == expected_source
         "recall5": bool,            # 任一块 text 含任一 key
         "top1": "rag-faq.md#0",
         "top1_score": 0.73,
         "matched_key": "300 到 800 字"}   # recall5 命中时填，方便人工核对

    注意：
      - 必须用传入的 index_path 反序列化，**不能读全局缓存**，否则 v1/v2 会串
      - retrieve.load_index 接受 index_path 参数，直接复用
      - 每题的 chunk 列表要重新从对应 npz 载入（只有 v1/v2 两个文件，加载 2 次即可）

    TODO(你): 实现。
    """
    vectors, chunks = load_index(Path(index_path))
    results = []
    for q in questions:
        hits = search(q["question"], vectors, chunks, top_k)
        top_chunk, top_score = hits[0] if hits else ({},0.0)
        top1 = top_chunk.get("chunk_id","")
        hit1_file = top_chunk.get("source") == q["expected_source"]

        match_key = None
        recall_k = False
        for chunk, _ in hits:
            if chunk.get("source") != q["expected_source"]:
                continue
            hit, key = _keys_hit(q, chunk.get("text", ""))
            if hit:
                recall_k = True
                match_key = key
                break
        results.append({
            "id": q["id"],
            "group": q.get("group", "?"),
            "hit1_file": hit1_file,
            "recall_k": recall_k,
            "top1": top1,
            "top1_score": float(top_score),
            "match_key": match_key,
        })
    return results


def _has_citation(answer: str, sources: list[dict]) -> bool:
    # 简单判断：答案里出现任一 source 的文件名，或出现 [数字] 标记
    if re.search(r"\[\d+\]", answer):
        return True
    for s in sources:
        src = s.get("source", "")
        if src and src in answer:
            return True
    return False

def eval_end_to_end(questions: list[dict], repeat: int = 1) -> list[dict]:
    """L2：每题独立 session 调 chat()，判断答案里有没有 keys。

    **每题一个新 session_id**（如 f"eval-{q['id']}-{i}"），绝不能复用。
    复用会引入记忆污染：前面的答案进上下文，后面的题不检索也能"答对"，
    那时你测的是记忆不是检索。

    对每题返回：
        {"id": "Q1", "answer_ok": bool, "cited": bool,
         "hallucinated_citation": bool,   # 标了来源但 keys 不在任何检索结果里
         "steps": int, "terminated_by": str, "answer": "..."}

    TODO(你): 实现。
    """
    results = []
    for q in questions:
        for i in range(repeat):
            session_id = f"eval-{q['id']}-{i}"
            result = chat(session_id, q["question"])
            answer = result.get("answer") or ""
            sources = result.get("sources")
            steps = result.get("steps")

            answer_ok, _ = _keys_hit(q, answer)
            cited = _has_citation(answer, sources)

            actual = {s.get("source", "") for s in (sources or [])}
            cited_names = set(re.findall(r"[A-Za-z0-9_\-]+\.md", answer))
            cited = bool(cited_names) or bool(re.search(r"\[\d+\]", answer))
            hallucinated = bool(cited_names - actual)   # 引用了本轮没检索到的文件名

            results.append({
                "id": q["id"],
                "group": q.get("group", "?"),
                "answer_ok": answer_ok,
                "cited": cited,
                "hallucinated_citation": hallucinated,
                "steps": len(steps),
                "terminated_by": result.get("terminated_by", "unknown"),
                # 记录本轮实际检索到的文件，事后才能判断"答对"是真检索到的还是凭参数知识
                "sources": sorted({s.get("source", "") for s in (sources or [])}),
                "answer": answer,
            })
    return results

def report(results: list[dict], group: str | None = None) -> str:
    """汇总成 markdown 表格，方便直接贴进 docs/eval.md。

    必须分开统计：
      - group="v1" 的 Hit@1 / Recall@5  → 这是**对照实验**，能说明语料扩大的影响
      - group="v2" 的单列一行          → 只说明"新增语料可检索"，不能当提升幅度
    """
    if not results:
        return "（无结果）"

    is_l1 = "hit1_file" in results[0]          # 兼容 L1/L2 两种行，main 里两层都调 report

    by_group: dict[str, list[dict]] = {}
    for r in results:
        g = r.get("group", group or "all")
        if group and g != group:               # group 参数当过滤器用，None = 全要
            continue
        by_group.setdefault(g, []).append(r)

    lines = []
    if is_l1:
        lines += ["| group | 题数 | Hit@1 | Recall@5 | 说明 |",
                  "| --- | --- | --- | --- | --- |"]
    else:
        lines += ["| group | 题数 | 答案命中 | 带引用 | 虚构引用 | 平均步数 |",
                  "| --- | --- | --- | --- | --- | --- |"]

    for g in sorted(by_group):                 # v1 天然排在 v2 前面
        rows = by_group[g]
        n = len(rows)
        if is_l1:
            h1 = sum(1 for r in rows if r["hit1_file"])
            rc = sum(1 for r in rows if r["recall_k"])
            note = ("对照实验组（原始 2 篇）" if g == "v1"
                    else "新增语料可检索性，不计入提升幅度")
            lines.append(f"| {g} | {n} | {h1}/{n} ({100*h1/n:.0f}%) "
                         f"| {rc}/{n} ({100*rc/n:.0f}%) | {note} |")
        else:
            ok = sum(1 for r in rows if r["answer_ok"])
            cited = sum(1 for r in rows if r["cited"])
            halluc = sum(1 for r in rows if r["hallucinated_citation"])
            avg_steps = sum(r.get("steps", 0) for r in rows) / n
            lines.append(f"| {g} | {n} | {ok}/{n} ({100*ok/n:.0f}%) | {cited}/{n} "
                         f"({100*cited/n:.0f}%) | {halluc}/{n} | {avg_steps:.1f} |")

    # 明细表：往 docs/eval.md 的 before/after top-1 列里填的时候对着抄
    lines += ["", "### 明细"]
    if is_l1:
        lines += ["| id | group | top1 | hit1 | recall | match_key |",
                  "| --- | --- | --- | --- | --- | --- |"]
        for r in sorted(results, key=lambda r: int(re.search(r"\d+", r["id"]).group())):
            if group and r.get("group", group) != group:
                continue
            lines.append(f"| {r['id']} | {r.get('group', '?')} | {r.get('top1', '')} "
                         f"| {'✓' if r['hit1_file'] else '✗'} "
                         f"| {'✓' if r['recall_k'] else '✗'} | {r.get('match_key') or '-'} |")
    else:
        lines += ["| id | 答案命中 | 带引用 | 虚构引用 | 步数 |",
                  "| --- | --- | --- | --- | --- |"]
        for r in sorted(results, key=lambda r: int(re.search(r"\d+", r["id"]).group())):
            if group and r.get("group", group) != group:
                continue
            lines.append(f"| {r['id']} | {'✓' if r['answer_ok'] else '✗'} "
                         f"| {'✓' if r['cited'] else '✗'} "
                         f"| {'⚠' if r['hallucinated_citation'] else '-'} | {r.get('steps')} |")

    return "\n".join(lines)
    


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--layer", choices=["l1", "l2"], default="l1")
    ap.add_argument("--index", default="data/index_v1.npz")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--out", default=None, help="结果 json 落盘路径")
    args = ap.parse_args()

    qs = load_questions()
    if args.layer == "l1":
        rows = eval_retrieval(qs, args.index, args.top_k)
    else:
        rows = eval_end_to_end(qs, args.repeat)

    print(report(rows))
    if args.out:
        Path(args.out).write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )
