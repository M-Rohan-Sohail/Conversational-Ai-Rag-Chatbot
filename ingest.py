import os
import sys
from Chroma_db import add_documents, reset_db

try:
    import PyPDF2
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


# ==========================================
# CHUNKING SETTINGS
# ==========================================
CHUNK_SIZE = 1000       # characters per chunk
CHUNK_OVERLAP = 100     # overlap between consecutive chunks
# ==========================================

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks for better embedding quality."""
    # Remove unpaired Unicode surrogates (common in PDF math symbols)
    text = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():           # skip empty/whitespace-only chunks
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks

def read_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            pt = page.extract_text()
            if pt:
                text += pt + "\n"
    return text.strip()

def ingest_file(file_path):
    print(f"Ingesting file: {file_path}")
    text = ""
    filename = os.path.basename(file_path)
    
    if file_path.endswith(".txt"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
        except Exception as e:
            print(f"Failed to read TXT {file_path}: {e}")
    elif file_path.endswith(".pdf"):
        if HAS_PYPDF:
            try:
                text = read_pdf(file_path)
            except Exception as e:
                print(f"Failed to read PDF {file_path}: {e}")
        else:
            print(f"Skipping PDF {file_path} because PyPDF2 is not installed.")
    
    if text:
        chunks = chunk_text(text)
        print(f"Read {file_path} -> {len(chunks)} chunks")
        add_documents(chunks, source_filename=filename)
        print(f"Successfully ingested {filename} ({len(chunks)} chunks) into Chroma DB.")
    else:
        print(f"No valid text extracted from {file_path}")

if __name__ == "__main__":
    # Check for --reset flag
    if "--reset" in sys.argv:
        print("Resetting Chroma DB (clearing all existing data)...")
        reset_db()
        print("Database cleared.\n")
