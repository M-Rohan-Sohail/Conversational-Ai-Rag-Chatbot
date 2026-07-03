from langfuse.openai import OpenAI
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env")

client = OpenAI(api_key=api_key)

def generate_llm_response(system_prompt, prompt, memory=None, trace_name=None, session_id=None, tags=None):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if memory:
        messages.extend(memory)
    messages.append({"role": "user", "content": prompt})

    kwargs = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.3
    }

    if trace_name:
        kwargs["name"] = trace_name

    metadata = {}
    if session_id:
        metadata["langfuse_session_id"] = session_id
    if tags:
        metadata["langfuse_tags"] = tags

    if metadata:
        kwargs["metadata"] = metadata

    completion = client.chat.completions.create(**kwargs)
    return completion.choices[0].message.content
