# syntax=docker/dockerfile:1
#
# Containerizes the Streamlit chat UI (app.py). This is the primary,
# container-friendly entry point of the project.
#
# admin_app.py can be run from the SAME image by overriding the CMD, e.g.:
#   docker run -p 8502:8502 <image> streamlit run admin_app.py --server.port=8502 --server.address=0.0.0.0
#
# main.py (CLI voice loop) is NOT container-friendly: it records from a live
# microphone (sounddevice) and plays audio back locally (pygame), both of
# which require a real audio device attached to the process. Run it on a
# host machine directly instead of inside this container.

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/app/.cache/huggingface \
    SDL_AUDIODRIVER=dummy \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# System packages:
#   build-essential/git - some ML deps fall back to source builds on unusual platforms
#   curl                - used by the HEALTHCHECK below
#   libgomp1            - OpenMP runtime needed by onnxruntime/ctranslate2 (chromadb, faster-whisper)
#   libportaudio2       - runtime lib for sounddevice (only exercised by main.py's CLI mode)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        libgomp1 \
        libportaudio2 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install a CPU-only torch build first. sentence-transformers depends on torch,
# and the default PyPI wheel bundles CUDA libraries that are unused here and
# add well over a gigabyte to the image.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model (Chroma_db.py) and the Whisper STT model
# (stt.py) at build time. This avoids a slow/failing first request if the
# container has restricted or no outbound internet access at runtime.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" \
 && python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"

COPY . .

# Runtime data directories (see .dockerignore — these are not copied from the
# build context and should be mounted as volumes for persistence).
RUN mkdir -p chroma_db uploaded_data audio_history

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
