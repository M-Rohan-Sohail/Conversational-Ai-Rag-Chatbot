from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")

def transcribe(audio_path):
    segments, _ = model.transcribe(audio_path)
    text = "".join([seg.text for seg in segments])
    return text.strip()