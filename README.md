# ✈️ SkyNode AI — Backend

**AMD Hackathon 2026 | Track 1: AI Agents & Agentic Workflows**

Hệ thống Multi-Agent backend thuần túy — không có UI, chạy trực tiếp trên **terminal Mac**.

---

## 📁 Cấu trúc folder

```
skynode_backend/
│
├── main.py               ← ★ Chạy file này — terminal interface + pipeline
│
├── flight_agent.py       ← FlightSearchAgent  (wrapper của flight_core.py)
├── miles_agent.py        ← MilesArchitectAgent (wrapper của miles_core.py)
├── concierge_agent.py    ← ConciergeAgent      (tổng hợp output cuối cùng)
│
├── flight_core.py        ← Core logic tìm chuyến bay + SerpApi (code gốc team bạn)
├── miles_core.py         ← Core logic tính dặm/miles       (code gốc của bạn)
│
├── requirements.txt      ← Tất cả dependencies
├── .env.example          ← Template biến môi trường → copy thành .env rồi điền key
└── README.md
```

---

## 🔄 Kiến trúc Pipeline

```
 User gõ query trên terminal
          │
          ▼
 ┌─────────────────────┐
 │  FlightSearchAgent  │  gọi SerpApi → trả về FlightSearchResult
 └────────┬────────────┘
          │  .to_miles_agent_input()
          ▼
 ┌──────────────────────────┐
 │  MilesArchitectAgent     │  tính miles/card bonus → rank theo ROI
 └────────┬─────────────────┘
          │  .to_concierge_context()
          ▼
 ┌──────────────────────────┐
 │  ConciergeAgent          │  tổng hợp → recommendation cuối
 └────────┬─────────────────┘
          │
          ▼
 In kết quả ra terminal
```

---

## ⚙️ Cài đặt & Chạy

### Bước 1 — Vào folder

```bash
cd skynode_backend
```

### Bước 2 — Tạo virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Bước 3 — Cài dependencies

```bash
pip install -r requirements.txt
```

### Bước 4 — Tạo file `.env`

```bash
cp .env.example .env
# Mở .env và điền VLLM_BASE_URL, MODEL_NAME, SERPAPI_KEY
```

| Key | Lấy ở đâu |
|-----|-----------|
| `VLLM_BASE_URL` | IP AMD droplet, ví dụ `http://123.45.67.89:8000/v1` |
| `MODEL_NAME` | Tên model vLLM đang chạy, ví dụ `Qwen/Qwen2.5-7B-Instruct` |
| `SERPAPI_KEY` | Đăng ký free tại [serpapi.com](https://serpapi.com) (100 searches/tháng) |

### Bước 5 — Chạy

```bash
python main.py
```

---

## 💬 Ví dụ tương tác trên terminal

```
You: Find flights from Hanoi to Tokyo on 2026-06-01

[Step 1/3] FlightSearchAgent — searching flights...
✅ Found 5 flights: HAN → NRT
   ⭐ Vietnam Airlines VN311    $520 | Economy | 0 stop(s) | 5h30m
      Singapore Airlines SQ177  $580 | Economy | 1 stop(s) | 8h15m
      Korean Air KE693           $490 | Economy | 1 stop(s) | 9h00m

[Step 2/3] MilesArchitectAgent — analyzing rewards for 'Chase Sapphire Reserve'...
✅ Miles analysis complete
   [BEST MILES  ] Singapore Airlines  $580 → eff. $529.35 | 1450 miles + 2900 pts
   [BEST VALUE  ] Korean Air          $490 → eff. $461.20 | 1225 miles + 1470 pts
   [STANDARD    ] Vietnam Airlines    $520 → eff. $497.25 |  975 miles + 1560 pts

[Step 3/3] ConciergeAgent — writing final recommendation...

════════════════════════════════════════════════════════════
🏆 Book Singapore Airlines SQ177 — highest rewards, effective cost $529
════════════════════════════════════════════════════════════

Why: SQ earns 1,450 miles + 2,900 Chase points ($50.65 value). Effective cost
     $529 vs Korean Air $461 — only $68 more but far better KrisFlyer upgrade path.

💳 Card: Chase Sapphire Reserve gives 3x points = $17.40 extra on this purchase.
✈️  Upgrade: 18,000/30,000 VN miles — need 12,000 more (~2-3 flights).
```

---

## 🔗 Tích hợp với Agent khác / Web dev

```python
from flight_agent import FlightSearchAgent
from miles_agent import MilesArchitectAgent

flight_agent = FlightSearchAgent(serpapi_key="your_key")
miles_agent  = MilesArchitectAgent()

flights = flight_agent.search_structured("HAN", "NRT", "2026-06-01")
result  = miles_agent.analyze_flights(
    flights=flights.to_miles_agent_input(),
    user_card="Chase Sapphire Reserve",
    current_miles=18000,
    current_miles_airline="Vietnam Airlines",
)

result.to_dict()              # → full JSON cho frontend render
result.to_concierge_context() # → short string cho Agent khác nhét vào prompt
```

---

## 🏗️ Tech Stack

| Component | Technology |
|-----------|-----------|
| GPU | AMD MI300X (192GB HBM3) |
| Inference | vLLM (OpenAI-compatible API) |
| LLM | Qwen2.5-7B-Instruct |
| Flight Data | SerpApi — Google Flights engine |
| Agent Pattern | Custom Agentic Loop + Function Calling |
| Language | Python 3.10+ |