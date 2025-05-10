import json
import os
import uuid
from pathlib import Path

import spacy
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# ─── Configuration ─────────────────────────────────────────────────────────────

JSON_PATH        = "articles.json"
# QDRANT_URL       = os.getenv("QDRANT_URL")
# QDRANT_API_KEY   = os.getenv("QDRANT_API_KEY")
# COLLECTION_NAME  = "articles"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MAX_TOKENS           = 512
OVERLAP_TOKENS       = 128
BATCH_SIZE           = 32

# ─── Load & Initialize ─────────────────────────────────────────────────────────

# 1. Load articles JSON
with open(JSON_PATH, encoding="utf-8") as f:
    articles = json.load(f)

# 2. spaCy for sentence splitting (French model; switch if needed)
nlp = spacy.load("fr_core_news_md")

# 3. HuggingFace tokenizer for MiniLM
tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)

# 4. SentenceTransformer embedder
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

# 5. Qdrant client & (re)create collection
# client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
# vector_dim = embedder.get_sentence_embedding_dimension()
# client.recreate_collection(
#     collection_name=COLLECTION_NAME,
#     vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE)
# )

# ─── Helper: Chunk with Overlap ─────────────────────────────────────────────────

def chunk_text(sentences, max_tokens=MAX_TOKENS, overlap=OVERLAP_TOKENS):
    chunks = []
    current_sents = []
    current_len = 0

    for sent in sentences:
        token_ids = tokenizer.encode(sent, add_special_tokens=False)
        tlen = len(token_ids)

        # If single sentence > max, truncate it
        if tlen > max_tokens:
            token_ids = token_ids[:max_tokens]
            sent = tokenizer.decode(token_ids)
            tlen = max_tokens

        # Flush chunk if adding this sentence would exceed limit
        if current_len + tlen > max_tokens:
            chunks.append(" ".join(current_sents))
            # build overlap: last `overlap` tokens
            flat_ids = tokenizer.encode(" ".join(current_sents), add_special_tokens=False)
            carry_ids = flat_ids[-overlap:]
            carry_text = tokenizer.decode(carry_ids)
            current_sents = [carry_text]
            current_len = len(carry_ids)

        current_sents.append(sent)
        current_len += tlen

    if current_sents:
        chunks.append(" ".join(current_sents))

    return chunks

# ─── Main: Embed & Upload ───────────────────────────────────────────────────────

buffer = []

for art_idx, art in enumerate(articles):
    title   = art["title"]
    content = art["content"]

    # Sentence-split
    doc = nlp(content)
    sents = [s.text.strip() for s in doc.sents if s.text.strip()]

    # Chunk with overlap
    text_chunks = chunk_text(sents)
    with open("log.txt", "a",encoding="utf-8") as log_file:
        log_file.write(f"Article {art_idx}: {title}\n")
        for chunk in text_chunks:
            log_file.write(f"  - {chunk}\n")

    # Embed & prepare points
    embeddings = embedder.encode(text_chunks, batch_size=BATCH_SIZE, show_progress_bar=False)
    for chunk_idx, vec in enumerate(embeddings):
        pt = PointStruct(
            id=str(uuid.uuid4()),
            vector=vec.tolist(),
            payload={
                "title": title,
                "article_index": art_idx,
                "chunk_index": chunk_idx
            }
        )
        buffer.append(pt)

        if len(buffer) >= BATCH_SIZE:
            #client.upsert(collection_name=COLLECTION_NAME, points=buffer)
            buffer = []

# Final flush
# if buffer:
    #client.upsert(collection_name=COLLECTION_NAME, points=buffer)
    #flush to log.txt
    # with open("log.txt", "a") as log_file:
    #     for point in buffer:
    #         log_file.write(f"{point}\n")
    # buffer = []

#print(f"✅ Uploaded {sum(len(chunk_text(nlp(a['content']).sents)) for a in articles)} chunks into '{COLLECTION_NAME}'.")
