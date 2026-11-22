"""在线链路的第一段：问题 → 向量 → 余弦 → top-k。

今天先做成一个能手动验证的函数，等 agent.py 写好再挂成工具。

跑法（ingest 成功后再跑）：
    .venv/Scripts/python.exe -m app.retrieve
"""
import json
from pathlib import Path

import numpy as np
from app.embedding import encode_query
INDEX_PATH = Path("data/index.npz")
CHUNKS_PATH = Path("data/chunks.jsonl")


def chunks_path_for(index_path: Path) -> Path:
    """data/index_v1.npz -> data/chunks_v1.jsonl，配对由代码保证，不靠人记。"""
    stem = index_path.stem.replace("index", "chunks", 1)
    return index_path.with_name(stem + ".jsonl")

def load_index(
    index_path: Path = INDEX_PATH, chunks_path: Path | None = None
) -> tuple[np.ndarray, list[dict]]:
    """读回向量矩阵和对应的文本块。

    返回 (vectors, chunks)：
      vectors: (N, 512) float32
      chunks:  list[dict]，顺序必须和 vectors 的行一一对应
    """
    chunks_path = chunks_path or chunks_path_for(index_path)
    data = np.load(index_path)
    vectors = data["vectors"]
    chunks = []
    with open(chunks_path,encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            chunks.append(json.loads(line))
    # assert vectors.shape[0] == len(chunks) , f"向量行数 {vectors.shape[0]} 与 chunk 数 {len(chunks)} 不一致"
    if vectors.shape[0] != len(chunks):
        raise ValueError(
            f"索引与块数不匹配：vectors {vectors.shape[0]} 行，chunks {len(chunks)} 条。"
            f"检查 {index_path} 和 {chunks_path} 是否配套。"
    )
    return vectors,chunks

def search(query: str, vectors: np.ndarray, chunks: list[dict], k: int = 5) -> list[tuple[dict, float]]:
    """给问题，返回 k 个最相关的块及其分数。

    步骤：
      1. 用 embedding.encode_query 编码 query（指令前缀在 embedding 模块里统一处理）
      2. 余弦相似度：因为都已归一化，所以 scores = vectors @ query_vec
      3. 取分数最高的 k 个下标（np.argsort 是升序，注意方向）
      4. 返回 [(chunk_dict, float(score)), ...]，按分数从高到低
    """
    if not query.strip() or len(chunks) == 0:
        return []
    q_vec = encode_query(query)
    scores = vectors @ q_vec
    top_idx = np.argsort(-scores)[:k]
    return [(chunks[i], float(scores[i])) for i in top_idx]

if __name__ == "__main__":
    vectors, chunks = load_index()
    for chunk, score in search("为什么召回不准要先查切分", vectors, chunks):
        print(f"{score:.4f}  {chunk['chunk_id']}  {chunk['text'][:30].replace(chr(10), ' ')}...")
