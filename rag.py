import PyPDF2
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import io

# Load embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")


def extract_text_from_pdf(pdf_file):
    text = ""
    if isinstance(pdf_file, (str, bytes)):
        reader = PyPDF2.PdfReader(pdf_file)
    else:
        pdf_bytes = pdf_file.read()
        pdf_stream = io.BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_stream)

    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def chunk_text(text, chunk_size=300):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))
    return chunks


def store_in_faiss(chunks):
    embeddings = embedder.encode(chunks, convert_to_numpy=True)
    dim = embeddings.shape[1]
    
    # Create FAISS index (L2 similarity, use IndexFlatIP for cosine)
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index, embeddings

#
def retrieve_from_faiss(query, index, chunks, top_n=2):
    query_vec = embedder.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_vec, top_n)
    return [chunks[i] for i in indices[0]]

def answer_query(query, pdf_file, top_n=2):
    # 1. Extract text
    text = extract_text_from_pdf(pdf_file)
    if not text.strip():
        return "⚠️ Could not extract text from PDF."

    # 2. Chunking
    chunks = chunk_text(text)

    # 3. Store in FAISS
    index, _ = store_in_faiss(chunks)

    # 4. Retrieve from FAISS
    top_chunks = retrieve_from_faiss(query, index, chunks, top_n)

    # 5. Construct answer
    context = "\n\n".join(top_chunks)
    response = f"📄 Based on the document, here are the most relevant parts:\n\n{context}"
    return response
