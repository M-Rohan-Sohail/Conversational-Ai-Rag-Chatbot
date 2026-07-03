import chromadb
from sentence_transformers import SentenceTransformer
import os
import hashlib

db_dir = os.path.join(os.path.dirname(__file__), "chroma_db")
client = chromadb.PersistentClient(path=db_dir)
collection = client.get_or_create_collection("docs")

embedder = SentenceTransformer("all-MiniLM-L6-v2")

BATCH_SIZE = 500  # Smaller batches for safer encoding + upsert

def add_documents(docs, source_filename="unknown"):
    if not docs:
        return
    # Sanitize: ensure all docs are non-empty strings
    docs = [str(d).strip() for d in docs if d and str(d).strip()]
    if not docs:
        return
    # Process in batches to avoid ChromaDB limits
    for i in range(0, len(docs), BATCH_SIZE):
        batch = docs[i:i + BATCH_SIZE]
        embeddings = embedder.encode(batch, show_progress_bar=True).tolist()
        
        ids = []
        for chunk in batch:
            h = hashlib.md5(chunk.encode()).hexdigest()[:10]
            # Replace spaces and special chars in filename for the ID just in case
            safe_name = source_filename.replace(" ", "_")
            ids.append(f"{safe_name}_{h}")
            
        metadatas = [{"source": source_filename} for _ in batch]
        
        collection.upsert(documents=batch, embeddings=embeddings, ids=ids, metadatas=metadatas)
        print(f"  Batch {i // BATCH_SIZE + 1}: upserted {len(batch)} chunks from {source_filename}")

def delete_documents_by_source(source_filename):
    try:
        collection.delete(where={"source": source_filename})
        print(f"Deleted documents from source: {source_filename}")
    except Exception as e:
        print(f"Failed to delete documents: {e}")

def retrieve(query, k=7):
    q_emb = embedder.encode([query]).tolist()
    results = collection.query(query_embeddings=q_emb, n_results=k)
    if not results or not results.get("documents") or not results["documents"][0]:
        return [], []
    return results["documents"][0], results["metadatas"][0]

def reset_db():
    """Delete and recreate the collection to start fresh."""
    global client, collection
    try:
        client.delete_collection("docs")
        print("Deleted existing 'docs' collection.")
    except Exception:
        print("No existing collection to delete.")
    collection = client.get_or_create_collection("docs")
    print("Created fresh 'docs' collection.")