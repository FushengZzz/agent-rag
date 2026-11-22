"""工具注册表。

两件事：
  1. TOOL_SCHEMAS —— 给模型看的说明书（JSON Schema，模型靠它决定调哪个工具）
  2. TOOL_FUNCS   —— 名字到真实函数的映射，dispatch 用它执行

面试常问：为什么工具描述要写"什么时候该用/不该用"？
因为模型只看这段文字选工具，描述含糊它就会选错。
"""
import re
import os
from app.retrieve import load_index, search
from dataclasses import dataclass, field
from pathlib import Path    

@dataclass
class ToolResult:
    content: str
    sources: list[dict] = field(default_factory=list)

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": (
                "在本地知识库里做语义检索，返回最相关的若干文本块及其来源。"
                "凡是涉及'文档里怎么说的''某个概念的定义/做法'都要用它。"
                "不要用它做数学计算，也不要用它查某份文件的全文。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索问题，用自然语言，不要只给关键词"},
                    "top_k": {"type": "integer", "description": "返回几条，默认 3，范围 1-10"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calc",
            "description": (
                "计算数学表达式，支持 + - * / ** 与括号。"
                "只在需要精确数值时使用；涉及文档内容的问题不要用它。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "如 '(450-50)*3'，只能包含数字和运算符"},
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup",
            "description": (
                "按文件名查看该文档的全部文本块，用于'这份文档讲了什么'这类整篇问题。"
                "已知具体问题、需要精准片段时用 search_docs，不要用它。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "文件名，如 rag-faq.md"},
                },
                "required": ["source"],
            },
        },
    },
]

# 懒加载：工具第一次被调用时才读索引，避免 import 阶段就吃 IO
_INDEX = Path(os.getenv("AGENT_INDEX", "data/index.npz"))
_INDEX_CACHE =None
def _get_index():
    global _INDEX_CACHE
    if _INDEX_CACHE is None:
        _INDEX_CACHE = load_index(_INDEX)
    return _INDEX_CACHE


def search_docs(query: str, top_k: int = 3) -> ToolResult:
    """检索并把结果拼成给模型读的文本，必须带来源，方便它标注引用。

    要求输出格式大致：
        [1] 来源 rag-faq.md（相似度 0.70）
        召回不准，先查哪一步……

        [2] 来源 agent-patterns.md（相似度 0.46）
        ……

    TODO(你): 用 _get_index() + search() 实现。
    """
    context = []
    vectors, chunks = _get_index()
    i = 1
    srcs = []
    for chunk, score in search(query, vectors, chunks, top_k):
        context.append(f"[{i}] 来源 {chunk['source']} (相似度 {score:.4f})\n{chunk['text']}")
        i += 1
        srcs.append({"chunk_id": chunk["chunk_id"], "source": chunk["source"], "score": score})
    return ToolResult(content="\n\n".join(context),sources=srcs) 


_ALLOWED = re.compile(r"^[0-9+\-*/().\s]+$")
def calc(expression: str) -> ToolResult:
    """计算表达式，返回结果字符串。

    ⚠️ 不要用裸 eval —— 模型可能传 '__import__("os").system(...)' 进来。
    允许的做法：白名单字符校验（只留数字和 +-*/(). 空格），或者用 ast 解析后只放行
    允许的节点类型。这一步就是"参数校验"，是面试会问的点。

    TODO(你): 实现。
    """
    if not _ALLOWED.fullmatch(expression):
        return ToolResult(content="错误：表达式含非法字符")
    try:
        return ToolResult(content=str(eval(expression)))
    except ZeroDivisionError:
        return ToolResult(content="错误：除数为零")
    except SyntaxError:
        return ToolResult(content="错误：表达式语法不正确")
    except Exception as e:
        return ToolResult(content=f"错误：{type(e).__name__}")


def lookup(source: str) -> ToolResult:
    """返回指定文件的全部文本块（按原顺序拼接）。

    TODO(你): 实现。文件不存在时返回一句明确的提示，不要抛异常。
    """
    vectors, chunks = _get_index()
    matched = [c["text"] for c in chunks if c["source"] == source]
    if  not matched:
        return ToolResult(content=f"错误,找不到文件 {source}, 可用文件为：{sorted(set(c['source'] for c in chunks))}")
    return ToolResult(content="\n\n".join(matched))


TOOL_FUNCS = {
    "search_docs": search_docs,
    "calc": calc,
    "lookup": lookup,
}


def dispatch(name: str, args: dict) -> ToolResult:
    """统一执行入口。

    三件事：
      1. 名字不在 TOOL_FUNCS 里 → 返回错误文本（不要抛异常，让模型知道并换路）
      2. 执行时任何异常 → 捕获，把错误信息作为结果返回给模型
      3. 结果过长 → 截断（工具返回几千字会一次把上下文吃掉）

    这样设计的原因：工具的失败应该是"模型能看见的一条消息"，而不是让整个进程崩掉。
    """
    func = TOOL_FUNCS.get(name)
    if func is None:
        return ToolResult(content=f"错误：没有名为 {name} 的工具，可用工具：{list(TOOL_FUNCS)}")

    try:
        result = func(**args)
    except TypeError as e:
        return ToolResult(content=f"错误：参数不匹配（{e}），请检查参数名和类型后重试")
    except Exception as e:
        return ToolResult(content=f"错误：工具 {name} 执行失败（{type(e).__name__}: {e}），请换一种方式或直接回答")

    content = result.content
    if len(content) > 2000:
        content = content[:2000] + "\n……（内容过长已截断）"
    return ToolResult(content=content, sources=result.sources)
