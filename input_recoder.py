import sounddevice as sd
import numpy as np

def record_audio_manual(sample_rate=16000):
    print("\n--- Press ENTER to START recording ---")
    input()
    
    audio_data = []
    recording = True
    
    def callback(indata, frames, time, status):
        if recording:
            audio_data.append(indata.copy())
            
    stream = sd.InputStream(samplerate=sample_rate, channels=1, callback=callback)
    with stream:
        print("🔴 RECORDING... --- Press ENTER to STOP ---")
        input()
        recording = False
        
    print("✅ Recording stopped. Processing...")
    if not audio_data:
        return np.array([])
    return np.concatenate(audio_data, axis=0).flatten()