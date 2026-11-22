"""FastAPI 入口：把 agent 暴露成 HTTP 服务。

跑法：
    .venv/Scripts/python.exe -m app.main
    然后打开 http://127.0.0.1:8000/docs 可以手动试接口

一个关键选择：路由用 def 而不是 async def。
因为 chat() 里面是**阻塞**调用（embedding 编码、LLM 请求），写成 async def
会堵住事件循环，所有请求排队。用 def，FastAPI 会自动丢到线程池里跑。
—— 面试问"为什么不全用 async"，这就是答案。
"""

import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import memory
from app.agent import chat
from app.ingest import build_index

app = FastAPI(title="agent-rag", version="0.1.0")


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    session_id: str | None = None      # 不传就新开一个会话


class AskResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[dict]
    steps_count: int
    terminated_by: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """问一句，拿答案。

    步骤：拿/建 session_id → 调 chat() → 组装响应。

    TODO(你): 实现。注意 chat() 返回的 dict 里有 answer/sources/steps/terminated_by，
              响应里只透出必要字段，别把整个 steps 返回给前端（太大）。
    """
    # 拿/建 session_id 
    session_id = req.session_id or uuid.uuid4().hex

    # 调chat()
    result = chat(session_id, req.question)

    # 组装响应
    return AskResponse(
        answer=result.get("answer") or "",
        session_id=session_id,
        sources=result.get("sources") or [],
        steps_count=len(result.get("steps") or []),
        terminated_by=result.get("terminated_by") or "unknown",
    )

@app.post("/ingest")
def ingest():
    """重跑离线链路（重建索引）。

    这个接口是**阻塞**的：要读文件、编码、写盘，语料多时可能十几秒。
    现在同步执行即可，语料变大再改成 BackgroundTasks + 任务状态查询。

    TODO(你): 实现。返回 build_index 的统计信息（文档数、块数、维度）。
              注意 build_index 现在只 print 不返回，要么改它的返回值，要么在这里重新统计。
    """
    stats = build_index()
    return {"status": "ok", **stats}


@app.get("/sessions/{session_id}")
def session_info(session_id: str):
    """调试用：看某个会话的摘要和剩余轮数。

    这个接口是给你自己排查问题用的，面试演示时也可以展示"记忆确实在工作"。
    """
    sess = memory._sessions.get(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {
        "summary": sess["summary"],
        "messages": len(sess["messages"]),
        "turns": len(sess["messages"]) // 2,
    }


@app.delete("/sessions/{session_id}")
def clear_session(session_id: str):
    """清空会话（测试用）。"""
    memory.reset(session_id)
    return {"cleared": session_id}


# ---------------------------------------------------------------------------
# W3 再做的部分：流式
# ---------------------------------------------------------------------------
# @app.post("/ask/stream")
# def ask_stream(req: AskRequest):
#     """流式返回。
#
#     难点：现在 chat() 是"跑完 loop 才有结果"，没有 token 级流。
#     两条路：
#       a) 简单版：假流式——拿到完整答案后按字切片 yield，前端体验一样，
#          延迟没改善。适合赶时间。
#       b) 真流式：run_agent 里最后一次调用改用 stream=True，
#          用 StreamingResponse + SSE 逐块吐。要改 run_agent 的返回结构。
#     面试别把 a 说成 b，说清"当前是按字切片，真流式的改法是……"。
#     """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
