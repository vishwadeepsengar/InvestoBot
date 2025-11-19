import PyPDF2
import numpy as np
import faiss
import io
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

from chatbot import ask_groq_deepseek

# Load embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")


# --- 1️⃣ Extract Text from PDF ---
def extract_text_from_pdf(pdf_file):
    """
    Accepts:
      - file-like object (e.g. Streamlit uploaded file)
      - bytes
      - file path string
    Returns full extracted text.
    """
    text = ""

    if isinstance(pdf_file, (str, bytes)):
        reader = PyPDF2.PdfReader(pdf_file)
    else:
        # e.g. Streamlit UploadedFile
        pdf_bytes = pdf_file.read()
        pdf_stream = io.BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_stream)

    for page in reader.pages:
        text += page.extract_text() or ""
    return text


# --- 2️⃣ Extract Text from News Article URL (more robust) ---
def extract_text_from_url(url: str) -> str:
    """
    Fetches the web page and tries to extract the main article text.
    Uses:
      - custom User-Agent
      - <article> tag if present
      - fallback to all <p> tags
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[extract_text_from_url] Error fetching URL: {e}")
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove junk tags
    for tag in soup(["script", "style", "nav", "header", "footer", "form", "aside"]):
        tag.decompose()

    text = ""

    # 1️⃣ Try <article> tag (most news sites)
    article_tag = soup.find("article")
    if article_tag:
        paragraphs = article_tag.find_all("p")
        text = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)

    # 2️⃣ Some finance sites wrap content differently – try common container classes
    if not text.strip():
        # Example common patterns: "article-body", "caas-body", "story-content"
        possible_classes = [
            "caas-body",
            "article-body",
            "story-body",
            "story-content",
            "article-content",
            "post-content",
        ]
        for cls in possible_classes:
            div = soup.find("div", class_=cls)
            if div:
                paragraphs = div.find_all("p")
                text = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)
                if text.strip():
                    break

    # 3️⃣ Last fallback: all <p> tags on the page
    if not text.strip():
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)

    # Optional: tiny debug
    print(f"[extract_text_from_url] Extracted text length: {len(text)} characters")

    return text


# --- 3️⃣ Chunk Text into small blocks ---
def chunk_text(text, chunk_size=300):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks


# --- 4️⃣ Build FAISS Index ---
def store_in_faiss(chunks):
    embeddings = embedder.encode(chunks, convert_to_numpy=True)
    dim = embeddings.shape[1]

    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index, chunks


# --- 5️⃣ Retrieve Top Chunks for Query ---
def retrieve_from_faiss(query, index, chunks, top_n=3):
    query_vec = embedder.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_vec, top_n)
    return [chunks[i] for i in indices[0]]


# --- 6️⃣ Generic: Build Index from PDF or URL ---
def build_index_from_source(pdf_file=None, article_url: str = None, chunk_size=300):
    """
    Use EITHER:
      - pdf_file: uploaded PDF / path / bytes
      - article_url: link to a news article
    Returns: (index, chunks) or (None, None) if no text.
    """
    text = ""

    if article_url:
        text = extract_text_from_url(article_url)
    elif pdf_file is not None:
        text = extract_text_from_pdf(pdf_file)

    # Basic sanity check
    if not text or not text.strip():
        print("[build_index_from_source] No text extracted from source.")
        return None, None

    chunks = chunk_text(text, chunk_size=chunk_size)
    if not chunks:
        print("[build_index_from_source] Chunking produced no chunks.")
        return None, None

    index, chunks = store_in_faiss(chunks)
    return index, chunks


# --- 7️⃣ FINAL — Groq LLM + RAG Answer Function ---
def answer_with_rag(query, pdf_file=None, article_url: str = None, top_n=3):
    """
    RAG answer function that supports:
      - PDF input:    answer_with_rag(query, pdf_file=uploaded_pdf)
      - News URL:     answer_with_rag(query, article_url="https://...")
    """
    index, chunks = build_index_from_source(pdf_file=pdf_file,
                                            article_url=article_url)

    if index is None or not chunks:
        return "⚠️ Could not extract readable text from the provided source (PDF/URL)."

    top_chunks = retrieve_from_faiss(query, index, chunks, top_n)
    context = "\n\n---\n".join(top_chunks)

    prompt = f"""
You are InvestoBot, a financial education assistant.
Use STRICTLY the context below to answer:

📄 CONTEXT EXTRACT:
{context}

❓ USER QUERY:
{query}

🎯 RESPONSE STYLE RULES:
- Explain clearly in simple words
- Do not make claims outside the context
- If information is missing in the context, say so honestly
- Add at the end: "This is general educational information, not investment advice."
"""

    answer = ask_groq_deepseek(prompt)
    return answer
