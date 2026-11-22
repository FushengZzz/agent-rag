import os
from dotenv import load_dotenv

load_dotenv()
from sentence_transformers import SentenceTransformer
import numpy as np

EMBED_MODEL = "BAAI/bge-small-zh-v1.5"
model = SentenceTransformer(os.getenv("EMBED_MODEL",EMBED_MODEL))
QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："

def encode_docs(texts: list[str]) -> np.ndarray:
    return model.encode(texts, normalize_embeddings=True)

def encode_query(query: str) -> np.ndarray:
    return model.encode(QUERY_PREFIX + query, normalize_embeddings=True)