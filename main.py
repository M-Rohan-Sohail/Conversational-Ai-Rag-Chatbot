import numpy as np
from scipy.io.wavfile import write
import asyncio
import os
import time

from input_recoder import record_audio_manual
from stt import transcribe
from tts_service import tts_to_file, play_audio
from rag_pipeline import generate_response
from memory_saver import MemorySaver


def main():
    import uuid
    session_id = f"cli-session-{uuid.uuid4().hex[:8]}"
    memory_saver = MemorySaver()
    
    sample_rate = 16000
    print("CLI RAG Voice Assistant is ready.")
    
    # Ensure audio_history folder exists
    os.makedirs("audio_history", exist_ok=True)
    
    while True:
        audio_np = record_audio_manual(sample_rate)
        
        if len(audio_np) == 0:
            continue
            
        # Generate unique filenames using standard unix timestamps
        timestamp = int(time.time())
        input_file = f"audio_history/input_{timestamp}.wav"
        output_file = f"audio_history/output_{timestamp}.mp3"
            
        write(input_file, sample_rate, audio_np)
        
        text = transcribe(input_file)
        if text.strip() == "":
            print("No speech detected.")
            continue
            
        print("User:", text)
        response = generate_response(text, memory_saver, session_id=session_id)
        print("Bot:", response)

        # TTS async saving and playing 
        asyncio.run(tts_to_file(response, filename=output_file))
        play_audio(filename=output_file)

if __name__ == "__main__":
    main()