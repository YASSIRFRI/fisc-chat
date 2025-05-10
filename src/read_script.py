import chromadb

client = chromadb.PersistentClient(path="./db")
collection = client.get_collection(name="vector_db")
from langchain.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer


model = SentenceTransformer("louisbrulenaudet/lemone-gte-embed-max",trust_remote_code=True)


query = input("Enter your query: ")

query_vector = model.encode(query)

results = collection.query(query_embeddings=query_vector, n_results=2 , include=["documents"])

# Print results
for result in results["documents"]:
    for i in result:
        print(i)