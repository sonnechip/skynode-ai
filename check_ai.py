import requests

def debug_connection():
    print("--- 正在測試連線 ---")
    
    # 測試 Ollama
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        print(f"✅ Ollama 有回應！狀態碼: {r.status_code}")
        print(f"妳目前擁有的模型: {r.json()}")
    except Exception as e:
        print(f"❌ 無法連上 Ollama: {e}")

    # 測試 vLLM
    try:
        r = requests.get("http://localhost:8000/v1/models", timeout=3)
        print(f"✅ vLLM 有回應！狀態碼: {r.status_code}")
    except Exception as e:
        print(f"❌ 無法連上 vLLM (這沒關係，如果您現在沒開的話)")

if __name__ == "__main__":
    debug_connection()