import os
import requests
import re
from dotenv import load_dotenv

load_dotenv()  # loads GROQ_API_KEY from .env

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def ask_groq_deepseek(prompt: str) -> str:
    if not GROQ_API_KEY:
        return "Error: GROQ_API_KEY not set in environment / .env"

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            # use any Groq model you like, e.g.:
            # "llama-3.1-70b-versatile" OR "deepseek-r1-distill-llama-70b"
            "model": "llama-3.3-70b-versatile"
,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.7,
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        reply = data["choices"][0]["message"]["content"]

        # strip <think>...</think> if the model returns that
        reply_clean = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL).strip()
        return reply_clean

    except Exception as e:
        return f"Error contacting Groq API: {e}"
