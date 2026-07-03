import torch

device = torch.device("cpu")
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=False)
(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

def detect_speech(audio_np, sample_rate=16000):
    # audio_np = 1D numpy array
    if len(audio_np) < 512:
        return False
    speech_timestamps = get_speech_timestamps(audio_np, model, sampling_rate=sample_rate)
    return len(speech_timestamps) > 0