"""ReAct 主循环：模型决定调工具还是收尾。

这是整个项目最核心的一个文件，也是面试时能讲半小时的地方。

跑法：
    .venv/Scripts/python.exe -m app.agent

注意：system prompt 和工具定义放在最前面且**内容固定**，
只有用户问题在变。DeepSeek 有上下文缓存，前缀稳定才能命中，
命中部分的 token 价格更低（看 usage 里的 prompt_cache_hit_tokens）。
"""

import json
from app import memory
from app.tools.registry import TOOL_SCHEMAS, dispatch
from app.llm import MODEL, get_client


MAX_STEPS = 5

SYSTEM_PROMPT = """你是一个文档问答助手，只能依据工具检索到的内容回答。

规则：
1. 先判断是否需要查资料。涉及文档内容的问题，必须先调用 search_docs。
2. 拿到检索结果后，只用结果里的内容作答，并标注来源文件名。
3. 检索结果不包含答案时，直接说"文档里没有找到相关依据"，不要凭常识编造。
4. 同一个工具和参数不要重复调用；连续两次结果一样说明方向错了，换个说法或直接回答。
5. 回答简洁，不超过 200 字。
6. 只能为本轮工具返回的内容标注文件名来源。
   如果答案来自之前的对话记忆，就写"根据之前的对话"，绝对不要标注文档名。
   没有本轮检索结果时，宁可说"需要再查一下"。"""

client = get_client()
def chat(session_id: str, question: str) -> dict:
    history = memory.get_context(session_id)
    result = run_agent(question, history)
    memory.add_turn(session_id, question, result["answer"])
    return result

def run_agent(question: str, history: list[dict] | None = None) -> dict:
    """跑一轮问答，返回 {"answer": str, "steps": list, "sources": list}。

    steps 里记录每一步做了什么（调了哪个工具、参数、结果摘要），
    这份轨迹后面要写进日志、也要在面试时讲。

    循环结构（照着写，注释里是意图）：

        messages = [system] + history + [user]
        steps = []

        for step in range(MAX_STEPS):
            resp = client.chat.completions.create(
                model=MODEL, messages=messages,
                tools=TOOL_SCHEMAS, tool_choice="auto",
            )
            msg = resp.choices[0].message

            if 没有 tool_calls:
                # 模型收尾了
                return {"answer": msg.content, "steps": steps, ...}

            # 有 tool_calls：先把这条 assistant 消息原样塞回 messages
            # （不塞回去，模型下一轮就不知道"自己刚才要求调工具"）
            messages.append(msg)

            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)   # 注意：模型可能给出非法 JSON
                result = dispatch(tc.function.name, args)
                steps.append({...})
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        # 超出 MAX_STEPS：强制收尾，用已有信息回答，并说明未完成
        return {...}

    三个容易翻车的点（面试会问）：
      - msg 必须原样 append 回去，包括 tool_calls 字段
      - 模型的 arguments 是**字符串**，要 json.loads，而且可能解析失败
      - 步数上限到了不能直接抛异常，要给出"基于已有信息的回答"

    TODO(你): 按上面的结构实现。
    """
    system = {"role": "system", "content": SYSTEM_PROMPT}
    history = history or []
    user = {"role": "user", "content": question}
    messages = [system] + history + [user]
    steps = []
    sources = []
    seen = set()
    last_top_ids = None
    for step in range(MAX_STEPS):
        try:
            resp = client.chat.completions.create(
                model = MODEL, messages = messages,
                tools =TOOL_SCHEMAS, tool_choice ="auto",
                )
            msg = resp.choices[0].message 
        except Exception as e:
            answer = f"模型调用失败({type(e).__name__})，已获取 {len(sources)} 条来源，详见 steps"
            return {"answer": answer, "steps": steps, "sources": merge_sources(sources), "terminated_by": "error"}
        steps.append({"type": "llm_call", "step": step, "usage": resp.usage.model_dump(), "finish_reason": resp.choices[0].finish_reason})
        if not msg.tool_calls:
            # content 可能是 None（比如输出被 max_tokens 截断），兜一下再返回
            return {"answer": msg.content or "（模型未返回内容）", "steps": steps, "sources": merge_sources(sources), "terminated_by": "final"}
        messages.append(msg)
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError as e:
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": f"参数 JSON 解析失败：{e}，请检查格式重试"})
                steps.append({"tool" : tc.function.name, "error": "Bad JSON", "raw": tc.function.arguments[:200]})
                continue
            key = (tc.function.name, json.dumps(args, sort_keys=True, ensure_ascii=False))
            # 工具和参数是否重复检验
            if key in seen:
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": "该工具和参数已调用过，结果在上文，请换参数或直接回答"})
                continue
            seen.add(key)
            result = dispatch(tc.function.name, args)
            # search 结果收敛检验
            if tc.function.name == "search_docs" and result.sources:
                before = {s["chunk_id"] for s in sources}
                sources.extend(result.sources)
                new = {s["chunk_id"] for s in result.sources} - before
                result.content += f"\n本次检索新增 {len(new)} 条文本，其余与之前重复，请自行决定是否继续检索"
            steps.append({"tool": tc.function.name, "args": args, "result": result.content[:200]})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result.content})
    messages.append({"role": "system", "content": "已到达步数上限，请只基于以上获得的信息直接回答；如果信息不足以回答，明确说明还缺少什么，不要再请求调用工具。"})
    try:
        final = client.chat.completions.create(
            model=MODEL, messages=messages,
            tools=TOOL_SCHEMAS, tool_choice="none",
            max_tokens=500,
        )
        steps.append({
            "type": "llm_call",
            "step": "final",
            "forced": True,            # 关键：这是被强制收尾的
            "finish_reason": final.choices[0].finish_reason,
            "usage": final.usage.model_dump(),
        })
        answer = "[已达工具调用上限，以下为基于已有信息的回答]\n" + (final.choices[0].message.content or "")
    except Exception as e:
        answer = f"工具调用达上限且收尾失败（{type(e).__name__}），已获取 {len(sources)} 条来源，详见 steps"
    return {"answer": answer, "steps": steps, "sources": merge_sources(sources),"terminated_by": "max_steps"}

def merge_sources(items):
    best = {}
    for s in items:
        k = s["chunk_id"]
        if k not in best or s["score"] > best[k]["score"]:
            best[k] = s
    return sorted(best.values(),key=lambda s: -s["score"])

if __name__ == "__main__":
    """r1 = run_agent("为什么召回不准要先查切分？")
    print(json.dumps(r1, ensure_ascii=False, indent=2))

    print("=" * 40)
    r2 = run_agent("450 减 50 再乘 3 等于多少？")
    print(json.dumps(r2, ensure_ascii=False, indent=2))
    
    r3 = run_agent("先查切分，再查评测集，然后告诉我两件事的关系")
    print(json.dumps(r3, ensure_ascii=False, indent=2))
    """
    sid = "test"
    memory.reset(sid)
    questions = [
        "切分粒度怎么定？",
        "召回不准先查什么？",
        "怎么证明优化有效？",
        "上下文超长怎么办？",
        "第一轮你提到的切分粒度，具体是多少字？",
    ]
    for i, q in enumerate(questions):
        result = chat(sid,q,)
        print(json.dumps(result, ensure_ascii=False, indent=2))

