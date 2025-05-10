import os
import json
import time
import chromadb
import PyPDF2
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

# --- Configuration ---
load_dotenv()  # make sure OPENAI_API_KEY is in your .env
INPUT_JSON_PATH         = r"D:\bot_dgi\questions.json"
OUTPUT_JSON_PATH        = "./finetuning_dataset.json"
CHROMA_DB_PATH          = r"D:\bot_dgi\pdf-to-text-chroma-search\db"
CHROMA_COLLECTION_NAME  = "my_collection"
EMBEDDING_MODEL_NAME    = "louisbrulenaudet/lemone-gte-embed-max"
OPENAI_API_KEY          = os.getenv("OPENAI_API_KEY")
MAX_RETRIES             = 3
RETRY_DELAY             = 0  # seconds

# --- Init clients / models ---
openai_client = OpenAI(api_key=OPENAI_API_KEY)
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection    = chroma_client.get_collection(name=CHROMA_COLLECTION_NAME)
embed_model   = SentenceTransformer(EMBEDDING_MODEL_NAME, trust_remote_code=True)

# --- Load questions ---
with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
    questions_list = json.load(f).get("questions", [])


# --- Build fine‑tuning data ---
fine_tuning_data = []

for item in tqdm(questions_list, desc="Building examples"):
    question = item.get("question")
    if not question:
        continue

    # 1) Retrieve up to 2 context snippets from ChromaDB
    q_vec = embed_model.encode(question).tolist()
    hits = collection.query(
        query_embeddings=[q_vec],
        n_results=4,
        include=["documents"]
    )["documents"][0]
    if hits:
        context_string = "\n---\n".join(
            f"Extrait {i+1}:\n{doc}" for i, doc in enumerate(hits)
        )
    else:
        context_string = "Aucun extrait pertinent trouvé."

    # 2) Build the prompt template (French)
    prompt = f"""Vous êtes un assistant expert en droit fiscal marocain.  
Vos connaissances proviennent *exclusivement* du document Code Fiscal Marocain et des extraits ci‑dessous.  
Répondez de façon détaillée et rigoureuse à la question **UNIQUEMENT** à partir de ces informations. Indiquez explicitement la reference
utilise du context.

Contexte :
{context_string}

Question : {question}

Réponse :"""

    # 3) Query GPT‑4o
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = openai_client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": "Vous êtes un assistant AI."},
                    {"role": "user",   "content": prompt}
                ],
                temperature=0.0,
            )
            answer = resp.choices[0].message.content.strip()
            break
        except Exception as e:
            if attempt == MAX_RETRIES:
                answer = f"[ERREUR] Impossible d’obtenir une réponse : {e}"
            else:
                time.sleep(RETRY_DELAY)

    # 4) Add to dataset
    fine_tuning_data.append({
        "prompt": prompt,
        "completion": " " + answer  # leading space is recommended by OpenAI
    })

# --- Save to JSON for finetuning ---
with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump({"data": fine_tuning_data}, f, ensure_ascii=False, indent=2)

print(f"Dataset ready: {OUTPUT_JSON_PATH}")
