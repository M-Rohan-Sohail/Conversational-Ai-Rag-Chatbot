from Chroma_db import retrieve
from llm_openai import generate_llm_response

def generate_summary(topic):
    # Retrieve top 10 chunks from ChromaDB for summarization
    vector_docs = retrieve(topic, k=10)
    
    if not vector_docs:
        return f"I couldn't find sufficient context to summarize the topic: '{topic}'."
        
    context = "\n\n".join(vector_docs)
    
    system_prompt = "You are an expert summarization AI agent. Your task is to provide a highly accurate, comprehensive, and well-structured summary of the user's requested topic based strictly on the provided document context. Do not include outside knowledge."
    prompt = f"Topic to summarize: {topic}\n\nDocument Context:\n{context}\n\nPlease generate a thorough summary of the topic based on the context above."
    
    # We do not pass conversational memory here as it's a dedicated summarization task
    summary = generate_llm_response(system_prompt, prompt, memory=None)
    return summary
