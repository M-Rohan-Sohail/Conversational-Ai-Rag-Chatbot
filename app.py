import streamlit as st
import streamlit.components.v1 as components
import asyncio
import os
import time
import base64

# Import existing backend services
from stt import transcribe
from tts_service import tts_to_file
from rag_pipeline import generate_response
from memory_saver import MemorySaver
from analytics_db import init_analytics_db, log_query

# Initialize analytics DB
init_analytics_db()

# Set page configuration
st.set_page_config(page_title="Voice Assistant", layout="centered")

# Hide Streamlit Default Elements
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}
</style>
""", unsafe_allow_html=True)

# Custom Header HTML
header_html = """
<style>
.custom-header {
    background-color: #1a2f4c;
    color: white;
    padding: 15px 20px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    gap: 15px;
    width: 100%;
    max-width: 800px;
    box-sizing: border-box;
    justify-content: center;
    position: fixed;
    top: 1rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: 999;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
.header-logo {
    background-color: white;
    color: #1a2f4c;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-weight: bold;
    font-size: 20px;
}
.header-text {
    display: flex;
    flex-direction: column;
}
.header-title {
    font-size: 18px;
    font-weight: 600;
}
.header-subtitle {
    font-size: 12px;
    color: #4ade80;
    display: flex;
    align-items: center;
    gap: 5px;
}
.header-subtitle::before {
    content: '';
    display: inline-block;
    width: 8px;
    height: 8px;
    background-color: #4ade80;
    border-radius: 50%;
}
</style>
<div class="custom-header">
    <div class="header-logo">N</div>
    <div class="header-text">
        <div class="header-title">Customer Support Assistant</div>
        <div class="header-subtitle">Grounded AI Agent</div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# Initialize session state variables
if "memory_saver" not in st.session_state:
    st.session_state.memory_saver = MemorySaver()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = f"streamlit-session-{uuid.uuid4().hex[:8]}"

# Base CSS for Chat Bubbles
chat_css = """
<style>
.msg-row {
    display: flex;
    width: 100%;
    margin-bottom: 20px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.msg-row.user {
    justify-content: flex-end;
}
.msg-row.assistant {
    justify-content: flex-start;
    gap: 10px;
}
.msg-bubble {
    max-width: 75%;
    padding: 14px 18px;
    border-radius: 18px;
    font-size: 15px;
    line-height: 1.5;
    word-wrap: break-word;
}
.msg-bubble.user {
    background-color: #1f3c5e;
    color: white;
    border-bottom-right-radius: 4px;
}
.msg-bubble.assistant {
    background-color: white;
    color: #333;
    border-bottom-left-radius: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border: 1px solid #eaeaea;
}
.assistant-avatar {
    width: 38px;
    height: 38px;
    background-color: #e0e7ff;
    color: #1f3c5e;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 18px;
    flex-shrink: 0;
    margin-top: 5px;
    font-weight: bold;
}
.sources-container {
    margin-top: 15px;
    padding-top: 12px;
    border-top: 1px solid #f0f0f0;
}
.sources-title {
    font-weight: 600;
    font-size: 12px;
    margin-bottom: 8px;
    color: #444;
}
.source-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background-color: #f1f3f5;
    color: #495057;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 12px;
    margin-right: 6px;
    margin-bottom: 6px;
    border: 1px solid #dee2e6;
}
</style>
"""
st.markdown(chat_css, unsafe_allow_html=True)

# Display existing chat history
for i, msg in enumerate(st.session_state.chat_history):
    if msg["role"] == "user":
        # We need to replace newlines in content with <br> for HTML
        safe_content = msg["content"].replace("\\n", "<br>")
        st.markdown(f'<div class="msg-row user"><div class="msg-bubble user">{safe_content}</div></div>', unsafe_allow_html=True)
    else:
        safe_content = msg["content"].replace("\\n", "<br>")
            
        st.markdown(f'<div class="msg-row assistant"><div class="assistant-avatar">👩‍💼</div><div class="msg-bubble assistant">{safe_content}</div></div>', unsafe_allow_html=True)
        
        if "audio" in msg and i == len(st.session_state.chat_history) - 1:
            audio_path = msg["audio"]
            if os.path.exists(audio_path):
                with open(audio_path, "rb") as f:
                    audio_b64 = base64.b64encode(f.read()).decode("utf-8")
                    audio_html = f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3"></audio>'
                    st.markdown(audio_html, unsafe_allow_html=True)



# Declare the custom component
custom_input = components.declare_component("custom_input", path="custom_input_bar")

# Render the component
result = custom_input(key=f"custom_input_{st.session_state.turn_count}")

# Inject CSS to pin the component to the bottom and pad the chat
st.markdown("""
<style>
    .main .block-container {
        padding-bottom: 100px;
        padding-top: 100px;
    }
    iframe {
        position: fixed;
        bottom: 1rem;
        left: 50%;
        transform: translateX(-50%);
        width: 100%;
        max-width: 800px;
        z-index: 999;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

text_to_process = None
audio_output_file = None
timestamp = int(time.time())
query_type = "text"

if result:
    query_type = result.get("type", "text")
    if query_type == "text":
        text_to_process = result.get("data")
        
    elif query_type == "audio":
        audio_b64 = result.get("data")
        audio_bytes = base64.b64decode(audio_b64)
        
        os.makedirs("audio_history", exist_ok=True)
        input_file = f"audio_history/input_{timestamp}.webm"
        audio_output_file = f"audio_history/output_{timestamp}.mp3"
        
        with open(input_file, "wb") as f:
            f.write(audio_bytes)
            
        with st.spinner("Transcribing audio..."):
            text_to_process = transcribe(input_file)
            
        if not text_to_process or text_to_process.strip() == "":
            st.warning("No speech detected. Please try recording again.")

# Process the final text query
if text_to_process and text_to_process.strip() != "":
    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "content": text_to_process})

    # Render it immediately so the user sees their message while spinning
    safe_text = text_to_process.replace("\\n", "<br>")
    st.markdown(f'<div class="msg-row user"><div class="msg-bubble user">{safe_text}</div></div>', unsafe_allow_html=True)

    sources = []
    # Generate response from RAG
    with st.spinner("Thinking..."):
        try:
            start_time = time.time()
            response, sources = generate_response(
                text_to_process, 
                st.session_state.memory_saver, 
                session_id=st.session_state.session_id
            )
            latency_ms = (time.time() - start_time) * 1000
            
            # Log analytics
            was_answered = "decline" not in response.lower() and "sorry" not in response.lower()
            log_query(query_type, text_to_process, response, was_answered, latency_ms)
            
        except Exception as e:
            error_msg = str(e).lower()
            if "503" in error_msg or "over capacity" in error_msg or "overloaded" in error_msg:
                st.error("The server is currently overloaded. Please try again later.")
            else:
                st.error(f"Oops! Something went wrong: {e}")
            st.stop()

    bot_msg = {
        "role": "assistant",
        "content": response,
        "sources": sources
    }

    # Conditionally synthesize audio only if the input was audio
    if query_type == "audio":
        with st.spinner("Synthesizing voice..."):
            audio_output_file = f"audio_history/output_{timestamp}.mp3"
            os.makedirs("audio_history", exist_ok=True)
            asyncio.run(tts_to_file(response, filename=audio_output_file))
            bot_msg["audio"] = audio_output_file

    st.session_state.chat_history.append(bot_msg)
    st.session_state.turn_count += 1
    
    st.rerun()
