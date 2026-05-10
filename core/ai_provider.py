import os
import requests
from openai import OpenAI

def get_ai_config():
    # 在 WSL 裡，127.0.0.1 有時會失效。我們改用這個通配位址。
    # 如果妳有開 SSH 隧道，隧道會把遠端的 8000 對接到妳 WSL 的 127.0.0.1
    base_urls = ["http://127.0.0.1:8000/v1", "http://127.0.0.1:11434/v1"]
    
    # 嘗試連線 vLLM (遠端)
    try:
        # 強制不使用 Proxy，避免封包被擋
        resp = requests.get(base_urls[0] + "/models", timeout=0.5, proxies={'http': None, 'https': None})
        if resp.status_code == 200:
            return {
                "client": OpenAI(base_url=base_urls[0], api_key="not-required"),
                "model": os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
            }
    except:
        pass

    # 嘗試連線 Ollama (本地)
    try:
        resp = requests.get(base_urls[1].replace("/v1", "/api/tags"), timeout=0.5, proxies={'http': None, 'https': None})
        if resp.status_code == 200:
            return {
                "client": OpenAI(base_url=base_urls[1], api_key="ollama"),
                "model": "gemma4"
            }
    except:
        pass

    return None