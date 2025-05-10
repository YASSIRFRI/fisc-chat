import os
import PyPDF2
import chromadb
from sentence_transformers import SentenceTransformer

def pdf_pages_with_overlap(file_path, overlap=100):
    reader = PyPDF2.PdfReader(open(file_path, 'rb'))
    prev_tail = ""
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        # prepend last `overlap` chars of previous page
        if i > 0:
            text = prev_tail + text
        # remember this page’s tail for next iteration
        prev_tail = text[-overlap:]
        yield i, text

# load your embedder
model = SentenceTransformer("louisbrulenaudet/lemone-gte-embed-max", trust_remote_code=True)

# init Chroma
client     = chromadb.PersistentClient(path="./db")
collection = client.create_collection(name="vector_db")

for filename in os.listdir('./input'):
    if not filename.lower().endswith('.pdf'):
        continue

    docs, embs, ids = [], [], []
    for page_num, page_text in pdf_pages_with_overlap(os.path.join('./input', filename), overlap=100):
        vec = model.encode(page_text)
        docs.append(page_text)
        embs.append(vec)
        ids.append(f"{filename}#page{page_num}")
    print(f"Page_num {page_num}")

    collection.add(
        embeddings=embs,
        documents=docs,
        ids=ids
    )
