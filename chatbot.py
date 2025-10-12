import requests
import re

# -------------------------------
# Chatbot function using GPT4All local server
# -------------------------------
def ask_local_gpt4all(prompt):
    try:
        url = "http://localhost:4891/v1/chat/completions"  # Local GPT4All REST API
        payload = {
            "model": "DeepSeek-R1-Distill-Qwen-1.5B",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        }
        resp = requests.post(url, json=payload)
        data = resp.json()
        reply = data["choices"][0]["message"]["content"]

        # Remove <think> tags
        reply_clean = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL).strip()
        return reply_clean
    except Exception as e:
        return f"Error: {e}"
