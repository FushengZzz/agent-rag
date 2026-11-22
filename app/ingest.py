"""离线链路：文档 → 文本 → 切分 → 向量 → 落盘。

对应 docs/architecture.md 的"离线链路"5 个节点。
今天只做 markdown/纯文本，PDF 解析放到后面。

跑法：
    .venv/Scripts/python.exe -m app.ingest
"""
import json
from pathlib import Path
import numpy as np
from app.embedding import encode_docs

EXTRA_DIR = Path("data/append") 
RAW_DIR = Path("data/raw")
INDEX_PATH = Path("data/index.npz")
CHUNKS_PATH = Path("data/chunks.jsonl")

# 已知简化：这里按"字符数"切，不是真正的 token 数。
# 原因是不想为切分再引入 tokenizer 依赖，中文场景下字符数也够用。
# 这个取舍要写进 docs/decisions.md。
CHUNK_SIZE = 450


def chunks_path_for(index_path: Path) -> Path:
    """data/index_v1.npz -> data/chunks_v1.jsonl，配对"""
    stem = index_path.stem.replace("index", "chunks", 1)
    return index_path.with_name(stem + ".jsonl")

def load_documents(raw_dir: Path = RAW_DIR, extra_dir: Path | None = None) -> list[dict]:
    """读取目录下所有 .md / .txt。

    返回 list[dict]，每项形如：
        {"source": "rag-faq.md", "page": None, "text": "全文内容"}
    page 现在一律 None，等接了 PDF 再填真实页码。
    """
    docs = []
    dirs = [raw_dir] +([extra_dir] if extra_dir else [])
    for d in dirs:
        if not d.exists():
            continue
        for path in sorted(d.glob("*")):
            if path.suffix.lower() not in {".md", ".txt"}:
                continue 
            content = path.read_text(encoding="utf-8")
            docs.append({"source": path.name, "page": None, "text": content})
    return docs


def split_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """按段落聚合把长文本切成块。

    - 以空行（\n\n）为段落边界聚合段落，块大小约 size
    - 超长段（> size）在段内硬切
    - < MIN_CHUNK 的短块并入上一块
    - 相邻块不重叠

    TODO(你): 实现它。
    进阶（今天不要求）：优先在换行或句号处断开，而不是硬切在字中间。
    """
    text = text.replace("\r\n","\n")
    paragraphs = text.split("\n\n")
    paras = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(p) <= size:
            paras.append(p)
        else:
            for s in range(0,len(p),size):
                piece = p[s:s+size].strip()
                if piece:
                    paras.append(piece)
    
    merged_paras = []
    i = 0 
    while i < len(paras):
        p = paras[i]
        if p.startswith("#") and i + 1 < len(paras) and not paras[i+1].startswith("#"):
            merged_paras.append(p + "\n" +paras[i+1])
            i += 2
        else :
            merged_paras.append(p)
            i += 1
    paras = merged_paras
    chunks = []
    buf = ""
    for p in paras:
        if p.startswith("#") and buf:
            chunks.append(buf)
            buf = p
        elif not buf:
            buf = p
        elif len(buf) + 1 +len(p) <=size:
            buf = buf + "\n" +p
        else:
            chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)
    MIN_CHUNK = 80
    merged = []
    pending = None
    for c in chunks:
        if pending is not None:
            # 上一块是文件开头的短块（文档标题），并到这一块前面
            c = pending + "\n" + c
            pending = None

        if len(c) < MIN_CHUNK:
            if merged and len(merged[-1]) + 1 + len(c) <= size:
                merged[-1] = merged[-1] + "\n" + c
            elif not merged:
                pending = c
            else:
                merged.append(c)
        else:
            merged.append(c)

    if pending is not None:
        # 整个文档只有标题的情况，兜底
        merged.append(pending)
    return merged


def build_index(index_path: Path = INDEX_PATH, with_append: bool = False) -> dict:
    """串起三步并落盘。

    做四件事：
      1. load_documents → split_text → 摊平成 (文本块列表, 元数据列表)
      2. encode 所有文本块
      3. np.savez(INDEX_PATH, vectors=向量矩阵)
      4. 每行一个 json 写入 CHUNKS_PATH（ensure_ascii=False）
      5. 打印：文档数、块数、向量 shape

    TODO(你): 实现它。写完先跑一次，把输出贴出来。
    """
    chunks_path = chunks_path_for(index_path)
    docs = load_documents(RAW_DIR, EXTRA_DIR if with_append else None)
    chunks: list[dict] = []
    for doc in docs:
        pieces = split_text(doc["text"])
        i = 0
        for piece in pieces:
            chunks.append({
                "chunk_id": f"{doc['source']}#{i}",
                "source": doc["source"],
                "text": piece,
                })
            i=i+1
    texts = [c["text"]for c in chunks]
    vectors = encode_docs(texts)
    np.savez(index_path, vectors=vectors)
    with open(chunks_path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c,ensure_ascii=False)+"\n")
    print(f"文档数: {len(docs)}")
    print(f"块数:   {len(chunks)}")
    print(f"向量 shape: {vectors.shape}")
    return {"documents": len(docs),"chunks": len(chunks),"dim": int(vectors.shape[1])}

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--index",type=Path, default=INDEX_PATH, help="索引输出路径")
    parser.add_argument("--with-append", action="store_true", help="是否把 data/append 也纳入语料")
    args = parser.parse_args()
    build_index(args.index,args.with_append)
