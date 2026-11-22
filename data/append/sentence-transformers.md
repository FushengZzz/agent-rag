# Sentence Transformers: Embeddings, Retrieval, and Reranking

This framework provides an easy method to compute embeddings for accessing, using, and training state-of-the-art embedding and reranker models. It can be used to compute embeddings using Sentence Transformer models ([quickstart](https://sbert.net/docs/quickstart.html#sentence-transformer)), to calculate similarity scores using Cross-Encoder (a.k.a. reranker) models ([quickstart](https://sbert.net/docs/quickstart.html#cross-encoder)),

 to generate sparse embeddings using Sparse Encoder models ([quickstart](https://sbert.net/docs/quickstart.html#sparse-encoder)) or to compute token-level embeddings for ColBERT-style late-interaction retrieval using Multi-Vector Encoder models ([quickstart](https://sbert.net/docs/quickstart.html#multi-vector-encoder)). This unlocks a wide range of applications,

 including [semantic search](https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html), [semantic textual similarity](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html), and [paraphrase mining](https://sbert.net/examples/sentence_transformer/applications/paraphrase-mining/README.html).
### Embedding Models

First download a pretrained embedding a.k.a. Sentence Transformer model.

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
```

Then provide some texts to the model.

```python
sentences = [
    "The weather is lovely today.",
    "It's so sunny outside!",
    "He drove to the stadium.",
]
embeddings = model.encode(sentences)
print(embeddings.shape)
# => (3, 384)
```

And that's already it. We now have numpy arrays with the embeddings, one for each text. We can use these to compute similarities.

```python
similarities = model.similarity(embeddings, embeddings)
print(similarities)
# tensor([[1.0000, 0.6660, 0.1046],
#         [0.6660, 1.0000, 0.1411],
#         [0.1046, 0.1411, 1.0000]])
```
