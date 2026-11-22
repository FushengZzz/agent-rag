"""会话记忆：保留最近若干轮原文，更早的压成摘要。

三个设计取舍（每个都是面试题）：

1. 为什么只在进程内存：单机 demo，重启丢历史可接受；上生产要落 Redis。
   代价要说得出来，不要假装这是"设计良好"。

2. 为什么保留最近 N 轮原文、不全摘要：最近几轮往往决定当前问题的指代
   （"它""那个方案""刚才说的第二步"），摘要会把这些细节抹平。

3. 为什么不把摘要拼进 system prompt：system prompt + 工具定义是**稳定前缀**，
   能命中 DeepSeek 的上下文缓存（当前实测命中率 77.6%）。摘要每轮都在变，
   拼进前缀会让缓存整段失效。所以摘要单独作为一条消息，放在 system **之后**。
   —— 这一条最能体现你懂缓存，面试值得主动讲。

会话在内存里的形状：
    _sessions[session_id] = {
        "summary": str,          # 早期对话的摘要，可能为空
        "messages": list[dict],  # 最近几轮的原始消息，role/content
    }
一轮 = 一条 user + 一条 assistant。
"""

from app.llm import MODEL, get_client

KEEP_TURNS = 3            # 保留原文的轮数
SUMMARY_MAX_CHARS = 200   # 摘要长度上限

SUMMARY_PROMPT = """你在压缩一段多轮对话的历史记录。

要求：
1. 保留：用户提出的具体问题、得到的事实性结论、用户的偏好或限制条件。
2. 丢弃：寒暄、重复表述、工具调用的中间过程、已经解决的推理步骤。
3. 用第三人称陈述，不要写成对话。
4. 不超过 {limit} 字。如果已有摘要，把新内容并入旧摘要，不要重复。

已有摘要：
{old_summary}

待压缩的对话：
{transcript}
"""

_sessions: dict[str, dict] = {}


def _new_session() -> dict:
    return {"summary": "", "messages": []}


def get_context(session_id: str) -> list[dict]:
    """取出该会话要注入到 messages 里的历史。

    返回：
      - 有摘要时：[{"role": "system", "content": "【对话摘要】..."}] + 最近几轮消息
      - 无摘要时：最近几轮消息（可能为空列表）

    注意：摘要那条用 role="system"，但要放在 agent 的 system prompt **后面**，
    不能塞进 system prompt 里面 —— 否则前缀变了，缓存失效。

    TODO(你): 实现。若 session_id 不存在，返回空列表。
    """
    content = []
    if session_id in _sessions and _sessions[session_id]["summary"]:
        content.append({"role": "system", "content": f"[对话摘要]{_sessions[session_id]['summary']}"})
    if session_id in _sessions and _sessions[session_id]["messages"]:
        content.extend(_sessions[session_id]["messages"])
    return content

def add_turn(session_id: str, question: str, answer: str) -> None:
    """记录一轮问答，必要时触发压缩。

    步骤：
      1. 取出（或新建）会话
      2. append({"role": "user", ...}) 和 {"role": "assistant", ...}
      3. 如果 messages 里的轮数 > KEEP_TURNS，调用 _compress

    TODO(你): 实现。注意轮数 = len(messages) // 2。
    """
    if session_id not in _sessions:
       _sessions[session_id] =  _new_session()
    _sessions[session_id]["messages"].append({"role": "user", "content": question})
    _sessions[session_id]["messages"].append({"role": "assistant", "content": answer})
    if len(_sessions[session_id]["messages"])//2 > KEEP_TURNS:
        try:
            _compress(session_id)
        except Exception:
            pass


def _compress(session_id: str) -> None:
    """把最旧的对话压成摘要，只保留最近 KEEP_TURNS 轮原文。

    步骤：
      1. 算出要压缩的部分：messages[:-KEEP_TURNS*2]，剩下的作为 recent 保留
      2. 把待压缩部分拼成 transcript（形如 "用户：……\\n助手：……"）
      3. 用 SUMMARY_PROMPT 调模型，max_tokens 给 300 左右、temperature=0
      4. 成功 → session["summary"] = 新摘要；session["messages"] = recent
      5. **失败 → 什么都不改**（网络挂了、余额不足都要降级，不能因为摘要失败丢历史）

    为什么 temperature=0：摘要要稳定可复现，不需要创造性。

    TODO(你): 实现。压缩失败时务必保住原 messages。
    """
    compress = _sessions[session_id]["messages"][:-KEEP_TURNS*2]
    recent = _sessions[session_id]["messages"][-KEEP_TURNS*2:]
    transcript = ""
    for message in compress:
        if message["role"] == "user":
            transcript += f"用户: {message['content']}\n"
        if message["role"] == "assistant":
            transcript += f"助手: {message['content']}\n"
    client = get_client()
    prompt = SUMMARY_PROMPT.format(limit = SUMMARY_MAX_CHARS, old_summary = _sessions[session_id]["summary"], transcript = transcript)
    try:
        resp = client.chat.completions.create(
                    model=MODEL, messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0
                )
    except Exception as e:
        # 压缩失败保持原样：不能因为摘要失败把历史弄丢
        print(f"[memory] 摘要失败，保留原历史：{type(e).__name__}: {e}")
        return
    content = resp.choices[0].message.content
    _sessions[session_id]["summary"] = content
    _sessions[session_id]["messages"] = recent



def reset(session_id: str | None = None) -> None:
    """清空会话。session_id 为 None 时清空全部。测试用。"""
    if session_id is None:
        _sessions.clear()
    else:
        _sessions.pop(session_id, None)


if __name__ == "__main__":
    # 造 5 轮对话，观察压缩前后的 messages 条数和摘要内容
    sid = "test"
    reset(sid)
    questions = [
        "什么是 RAG？",
        "切分粒度怎么定比较好？",
        "召回不准应该先查什么？",
        "怎么证明我的优化有效？",
        "那上下文超长了怎么办？",
    ]
    for i, q in enumerate(questions):
        add_turn(sid, q, f"（第{i + 1}轮的回答占位）")
        s = _sessions[sid]
        print(f"第{i + 1}轮后：messages={len(s['messages'])} 条，"
              f"summary={len(s['summary'])} 字")

    print("---- 摘要 ----")
    print(_sessions[sid]["summary"])
    print("---- 注入给 agent 的历史 ----")
    for m in get_context(sid):
        print(m["role"], ":", m["content"][:60])
