from Chroma_db import retrieve
from sqlite_db import retrieve_sql
from llm_openai import generate_llm_response
from summarization_agent import generate_summary
import re

# ============================================================
# SECURITY: Input validation — block malicious queries early
# ============================================================
# These patterns catch dangerous user intents BEFORE they reach
# the SQL generator or any other backend component.
DANGEROUS_PATTERNS = [
    # Database destruction commands
    r"\bdrop\b.*\b(table|database|schema|index|collection)\b",
    r"\bdelete\b.*\b(all|everything|table|database|data|record|row)\b",
    r"\btruncate\b",
    r"\bdestroy\b",
    r"\bwipe\b.*\b(data|database|table|everything)\b",
    r"\bclear\b.*\b(all|database|table|data|everything)\b",
    r"\bremove\b.*\b(all|everything|table|database|data)\b",
    r"\berase\b.*\b(all|everything|database|data)\b",
    # Database modification commands
    r"\binsert\b.*\binto\b",
    r"\bupdate\b.*\bset\b",
    r"\balter\b.*\btable\b",
    r"\bcreate\b.*\b(table|database|index)\b",
    r"\breplace\b.*\binto\b",
    # System exploitation
    r"\bexecute\b.*\b(command|script|code|sql|query)\b",
    r"\brun\b.*\b(command|script|sql|query)\b",
    r"\bsql\b.*\binjection\b",
    r"\bbypass\b.*\b(security|filter|validation)\b",
    r"\bhack\b",
    r"\bexploit\b",
    r"\bshell\b.*\b(command|access)\b",
    r"\bsystem\b.*\b(command|access|prompt)\b",
    # Prompt injection attempts
    r"\bignore\b.*\b(previous|above|prior)\b.*\b(instruction|prompt|rule)\b",
    r"\bforget\b.*\b(instruction|rule|prompt)\b",
    r"\boverride\b.*\b(instruction|rule|safety)\b",
    r"\bdisregard\b.*\b(instruction|rule|safety)\b",
]


def validate_query(query):
    """
    SECURITY GATE: Validates user input before processing.
    Returns (is_safe, reason) tuple.
    Checks for malicious patterns that could harm databases or exploit the system.
    """
    if not query or not query.strip():
        return False, "Empty query."

    query_lower = query.lower().strip()

    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, query_lower):
            return False, f"This query has been blocked for security reasons."

    return True, "Query is safe."


def analyze_intent(query):
    system_prompt = (
        "You are an intent classification system for a customer support assistant.\n"
        "Categorize the user's query into exactly one of four categories:\n"
        "GREETING_OR_CAPABILITY: The user is greeting you (e.g. 'hello', 'hi', 'hey', 'good morning'), asking who you are/your identity, or asking what you can do/assist with (e.g. 'what can you assist me with?', 'what can you do?', 'how can you help me?').\n"
        "SUMMARY: The user explicitly asks to summarize documents or a specific topic.\n"
        "DETAILED: The user explicitly asks for exact details, an exhaustive explanation, or an in-depth answer.\n"
        "NORMAL: Standard questions where the user wants a standard contextual answer, or general inquiries.\n"
        "Return ONLY the category name."
    )
    prompt = f"User query: {query}"
    response = generate_llm_response(system_prompt, prompt, memory=None, trace_name="intent-classification").strip().upper()
    
    if "GREETING_OR_CAPABILITY" in response:
        return "GREETING_OR_CAPABILITY"
    elif "SUMMARY" in response:
        return "SUMMARY"
    elif "DETAILED" in response:
        return "DETAILED"
    return "NORMAL"

def generate_response(query, memory_saver, session_id=None):
    # SECURITY: Validate the user's query before any processing
    is_safe, reason = validate_query(query)
    if not is_safe:
        blocked_response = "I'm sorry, I can't process that request. Your query appears to contain instructions that could harm the system. Please ask a genuine question about the available knowledge base."
        print(f"⚠️  QUERY BLOCKED: {reason} | Query: {query}")
        memory_saver.add_user(query)
        memory_saver.add_bot(blocked_response)
        return blocked_response, []

    intent = analyze_intent(query)
    
    if intent == "GREETING_OR_CAPABILITY":
        system_prompt = (
            "You are an expert customer support agent for the UK/Northern Ireland automotive dealer groups: Lookers, Charles Hurst, and Sytner Group. "
            "You naturally know about their dealerships, brands, services, history, and policies. "
            "Respond politely and describe how you can help (e.g., support with vehicle inquiries, dealership locations, aftersales services, policies, and employee benefits for Lookers, Charles Hurst, and Sytner Group). "
            "CRITICAL constraints:\n"
            "1. Speak as a natural representative of the dealerships. Do NOT mention 'context', 'provided documents', 'provided text', 'information provided', or similar phrases.\n"
            "2. Do NOT act as if the user provided you with documents/context."
        )
        prompt = f"User Question: {query}"
        response = generate_llm_response(
            system_prompt, 
            prompt, 
            memory_saver.get_memory(),
            trace_name="greeting-response",
            session_id=session_id,
            tags=["customer-support"]
        )
        memory_saver.add_user(query)
        memory_saver.add_bot(response)
        return response, []

    if intent == "SUMMARY":
        response = generate_summary(query)
        memory_saver.add_user(query)
        memory_saver.add_bot(response)
        return response, []
        
    # Retrieve from ChromaDB (Documents)
    vector_docs, vector_metas = retrieve(query)
    sources = list(set([m.get("source", "Unknown") for m in vector_metas if m and "source" in m])) if vector_metas else []
    
    # Retrieve from SQLite3 (Structured Data)
    sql_results = retrieve_sql(query)
    
    # Combine results
    context_parts = []
    if vector_docs:
        context_parts.append("--- Document Context ---\n" + "\n".join(vector_docs))
    if sql_results:
        context_parts.append("--- Database Context ---\n" + "\n".join(sql_results))
    
    context = "\n\n".join(context_parts)

    context_text = context if context.strip() else "No relevant information found in the knowledge base."

    if intent == "DETAILED":
        system_prompt = (
            "You are a highly detailed, exhaustive, and professional customer support agent for the automotive dealer groups Lookers, Charles Hurst, and Sytner Group. "
            "Provide a comprehensive answer based on the context. You MUST politely decline to answer any questions unrelated to these dealerships or customer support.\n"
            "CRITICAL constraints:\n"
            "1. Speak as a natural representative of the dealerships. Do NOT mention 'context', 'provided documents', 'provided text', 'information provided', or similar phrases.\n"
            "2. Do NOT act as if the user provided you with documents/context."
        )
    else:
        system_prompt = (
            "You are a helpful, concise, and friendly customer support agent for the automotive dealer groups Lookers, Charles Hurst, and Sytner Group. "
            "Keep your answers short. You MUST politely decline to answer any questions unrelated to these dealerships or customer support.\n"
            "CRITICAL constraints:\n"
            "1. Speak as a natural representative of the dealerships. Do NOT mention 'context', 'provided documents', 'provided text', 'information provided', or similar phrases.\n"
            "2. Do NOT act as if the user provided you with documents/context."
        )

    prompt = f"Context:\n{context_text}\n\nUser Question: {query}\n\nInstructions:\n1. Answer questions strictly using the Context.\n2. If the user asks something unrelated to these dealerships or Context, politely decline.\n3. Do not refer to the context, files, or information as being 'provided' or 'provided to you'."
        
    response = generate_llm_response(
        system_prompt, 
        prompt, 
        memory_saver.get_memory(),
        trace_name="support-agent",
        session_id=session_id,
        tags=["customer-support"]
    )

    memory_saver.add_user(query)
    memory_saver.add_bot(response)
    return response, sources