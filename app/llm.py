"""LLM 客户端单例。

为什么要单独一个文件：
  agent.py 会 import memory.py，如果 memory 又 import agent 拿 client，
  就是循环 import。客户端这种"谁都要用"的东西必须放在最底层。

顺带解决第二个问题：MODEL 名字只在这里定义一次。
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "deepseek-chat"

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key or "在这里填" in api_key:
            raise SystemExit("没读到 DEEPSEEK_API_KEY，检查 .env")
        _client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    return _client
