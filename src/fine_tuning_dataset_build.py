import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer
import json
import os
import time
from tqdm import tqdm 
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()  # Charge les variables d'environnement depuis le fichier .env

PDF_PATH = r"D:\bot_dgi\pdf-to-text-chroma-search\input\CGI_FR_2025 (1)_compressed.pdf"
INPUT_JSON_PATH = r"D:\bot_dgi\questions.json"
OUTPUT_JSON_PATH = "./finetuning_dataset.json"
CHROMA_DB_PATH = "./db"
CHROMA_COLLECTION_NAME = "my_collection"
EMBEDDING_MODEL_NAME = "louisbrulenaudet/lemone-gte-embed-max"
GEMINI_MODEL_NAME = "gemini-1.5-pro-latest"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 5  # seconds

print("Initializing components...")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set.")
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize ChromaDB Client
try:
    print(f"Connecting to ChromaDB at path: {CHROMA_DB_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    print(f"Getting collection: {CHROMA_COLLECTION_NAME}")
    collection = client.get_collection(name=CHROMA_COLLECTION_NAME)
    print("ChromaDB client initialized successfully.")
except Exception as e:
    print(f"Error initializing ChromaDB: {e}")
    exit(1)

# Load Embedding Model
try:
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, trust_remote_code=True)
    print("Embedding model loaded successfully.")
except Exception as e:
    print(f"Error loading embedding model: {e}")
    exit(1)

# Load input questions
try:
    print(f"Loading questions from: {INPUT_JSON_PATH}")
    with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        questions_list = data.get("questions", [])
        if not questions_list:
             raise ValueError(f"Could not find 'questions' key or list is empty in {INPUT_JSON_PATH}")
    print(f"Loaded {len(questions_list)} questions.")
except FileNotFoundError:
    print(f"Error: Input JSON file not found at {INPUT_JSON_PATH}")
    exit(1)
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {INPUT_JSON_PATH}")
    exit(1)
except Exception as e:
    print(f"Error loading questions: {e}")
    exit(1)

# --- Upload PDF to Gemini API ---
pdf_file_object = None
if not os.path.exists(PDF_PATH):
     print(f"Error: PDF file not found at {PDF_PATH}")
     exit(1)

print(f"Uploading PDF '{PDF_PATH}' to Google...")
try:
    pdf_file_object = genai.upload_file(path=PDF_PATH, display_name="Moroccan Tax Code PDF")
    print(f"PDF uploaded successfully. File URI: {pdf_file_object.uri}")
except Exception as e:
    print(f"Error uploading PDF file: {e}")
    exit(1)

# --- Process Questions and Generate Answers ---
fine_tuning_data = []
print(f"\nProcessing {len(questions_list)} questions...")

# Initialize Gemini Model
try:
    print(f"Initializing Gemini model: {GEMINI_MODEL_NAME}")
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    print("Gemini model initialized.")
except Exception as e:
    print(f"Failed to initialize Gemini model: {e}")
    exit(1)

for item in tqdm(questions_list, desc="Generating Answers"):
    question = item.get("question")
    if not question:
        print("Warning: Found item without a 'question' key, skipping.")
        continue

    print(f"\nProcessing question: {question}")

    # 1. Retrieve Context from ChromaDB (only 2 best matches)
    context_docs = []
    try:
        print("  Querying ChromaDB...")
        query_vector = embedding_model.encode(question).tolist()
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=2,  # Récupère au maximum 2 meilleures correspondances
            include=["documents"]
        )
        if results and results.get("documents") and results["documents"][0]:
             context_docs = results["documents"][0]
             print(f"  Retrieved {len(context_docs)} context snippets from ChromaDB.")
        else:
            print("  No relevant documents found in ChromaDB for this question.")
    except Exception as e:
        print(f"  Error querying ChromaDB: {e}")

    context_string = "\n---\n".join([f"Extrait de Contexte {i+1}:\n{doc}" for i, doc in enumerate(context_docs)]) if context_docs else "Aucun extrait de contexte pertinent trouvé dans le vector store."

    # 2. Construct Prompt for Gemini in French
    prompt = f"""
    Vous êtes un assistant expert spécialisé en droit fiscal marocain. Vos connaissances proviennent *exclusivement* du document PDF fourni (Code Fiscal Marocain) et des extraits de contexte récupérés via une recherche vectorielle.

    **Tâche :** Répondez de manière détaillée à la question suivante. Basez votre réponse *strictement* sur les informations disponibles dans le fichier PDF téléversé et les vecteurs de contexte fournis.

    **Fichier PDF téléversé :** {pdf_file_object.display_name if pdf_file_object else 'N/A'} [Référence interne : Vous avez accès au contenu de ce fichier]
    **Vecteurs de Contexte issus de la Recherche Documentaire :**
    ---
    {context_string}
    ---

    **Question :**
    {question}

    **Instructions pour le Format de Réponse :**
    1. Fournissez une réponse complète et détaillée dérivée *uniquement* du PDF et des extraits de contexte.
    2. Identifiez le numéro d'article *principal* du PDF qui soutient l'essentiel de votre réponse. Si plusieurs articles sont pertinents, choisissez celui qui est le plus central. Si l'information provient principalement des extraits de contexte sans numéros d'article clairs, indiquez-le.
    3. Structurez votre réponse *exactement* de la manière suivante :
       `Selon l'Article [Numéro d'Article Principal ou "Extraits de Contexte"] : [Votre réponse détaillée utilisant les informations du PDF et/ou des contextes]. Références Utilisées : (Article X, Article Y du PDF ; Extrait de Contexte Z)`
    4. Dans la partie "Références Utilisées", listez tous les articles spécifiques (ex. Article 5, Article 6 A) du PDF et/ou des extraits de contexte (ex. Extrait de Contexte 1, Extrait de Contexte 3) que vous avez utilisés pour formuler *l'intégralité* de la réponse.
    5. Soyez précis et assurez-vous que la réponse est directement étayée par les documents fournis. N'ajoutez pas d'informations externes ni ne faites d'hypothèses.

    **Réponse :**
    """

    # 3. Call Gemini API with Retry Logic and delay between calls
    generated_answer = None
    for attempt in range(MAX_RETRIES):
        try:
            print(f"  Calling Gemini API (Attempt {attempt + 1}/{MAX_RETRIES})...")
            response = model.generate_content([prompt, pdf_file_object])
            if response.parts:
                 generated_answer = response.text.strip()
                 print("  Gemini response received.")
            elif response.prompt_feedback and response.prompt_feedback.block_reason:
                 print(f"  Warning: Prompt blocked. Reason: {response.prompt_feedback.block_reason}")
                 generated_answer = f"Error: Content generation blocked ({response.prompt_feedback.block_reason})"
            else:
                 print("  Warning: Received empty response from Gemini.")
                 generated_answer = "Error: No content generated by the model."
            break  # Exit retry loop on success or explicit block/empty response

        except Exception as e:
            error_message = str(e)
            print(f"  Error calling Gemini API (Attempt {attempt + 1}/{MAX_RETRIES}): {error_message}")
            # If a 429 error is detected, use a 48 second delay; otherwise use default delay.
            if "429" in error_message:
                delay = 48
            else:
                delay = DEFAULT_RETRY_DELAY
            if attempt < MAX_RETRIES - 1:
                print(f"  Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("  Max retries reached. Skipping this question.")
                generated_answer = f"Error: Failed to generate answer after {MAX_RETRIES} attempts."

    # 4. Store the result and update the output file immediately
    if generated_answer:
         fine_tuning_data.append({
             "question": question,
             "answer": generated_answer
         })
         try:
             output_data = {"questions": fine_tuning_data}
             with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
                 json.dump(output_data, f, ensure_ascii=False, indent=2)
             print(f"  Saved progress to {OUTPUT_JSON_PATH}.")
         except Exception as e:
             print(f"  Error saving output JSON file: {e}")
    
    # Delay after each successful call to prevent rate limit issues
    print("  Waiting 10 seconds before processing the next question...")
    time.sleep(10)

print("\nScript finished.")
