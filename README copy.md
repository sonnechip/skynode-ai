# ✈️ AI Flight Agent

An AI-powered flight search chatbot built with **Streamlit**, **Ollama (LLaMA 3)**, and **SerpApi**. Supports natural language queries in English, Vietnamese, and Chinese.

---

## 📋 Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the App](#running-the-app)
- [How to Use](#how-to-use)
- [Supported Airports](#supported-airports)
- [Deploying to Streamlit Cloud](#deploying-to-streamlit-cloud)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

- 🤖 Natural language flight search (no need to fill out forms)
- 🌍 Multi-language support: English, Vietnamese, Chinese
- 🗓️ One-way and round-trip search
- 💰 Displays price, duration, stops, airline, and flight number
- ⭐ Highlights the best flight option automatically
- 📊 Session statistics (search count, message count)

---

## 🔧 Requirements

| Tool | Version |
|------|---------|
| Python | 3.9+ |
| Ollama | Latest |
| LLaMA 3 model | via Ollama |
| SerpApi account | Free or paid |

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ai-flight-agent.git
cd ai-flight-agent
```

### 2. Install Python dependencies

```bash
pip install streamlit ollama google-search-results python-dotenv
```

### 3. Install Ollama and pull LLaMA 3

Download Ollama from [https://ollama.com](https://ollama.com), then run:

```bash
ollama pull llama3
```

Make sure Ollama is running in the background before starting the app:

```bash
ollama serve
```

---

## ⚙️ Configuration

### Option A – Local `.env` file (for local development)

Create a `.env` file in the project root:

```env
SERPAPI_KEY=your_serpapi_key_here
```

Get your free API key at [https://serpapi.com](https://serpapi.com).

### Option B – Streamlit Cloud Secrets (for deployment)

In your Streamlit Cloud dashboard, go to **App Settings → Secrets** and add:

```toml
SERPAPI_KEY = your_serpapi_key_here
```

### Option C – Enter the key directly in the sidebar

You can also paste your SerpApi key into the **sidebar input field** at runtime. Click **🚀 Set Key** to apply it. This takes priority over the `.env` / Secrets configuration.

---

## ▶️ Running the App

```bash
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`.

---

## 💬 How to Use

Type your flight request naturally into the chat box. Examples:

**English:**
```
Find me a flight from Hanoi to Singapore on 2025-08-15
```

**Vietnamese:**
```
Tìm vé máy bay từ Hà Nội đến Bangkok ngày 20 tháng 7
```

**Round trip:**
```
Book a round trip from Ho Chi Minh to Tokyo, depart July 10, return July 20, 2 adults
```

The agent will extract the origin, destination, date, number of passengers, and trip type automatically, then display available flights as cards.

For general questions (not flight searches), the assistant will respond conversationally using LLaMA 3.

---

## 🗺️ Supported Airports

The app recognizes city names and IATA codes. Supported locations include:

| City | IATA Code |
|------|-----------|
| Hanoi / Hà Nội | HAN |
| Ho Chi Minh / Saigon | SGN |
| Da Nang | DAD |
| Phu Quoc | PQC |
| Bangkok | BKK |
| Singapore | SIN |
| Tokyo | NRT |
| Osaka | KIX |
| Seoul / Incheon | ICN |
| Taipei / Taiwan | TPE |
| Hong Kong | HKG |
| London | LHR |
| Paris | CDG |
| New York | JFK |
| Los Angeles | LAX |

You can also type IATA codes directly (e.g., `HAN`, `SGN`).

---

## ☁️ Deploying to Streamlit Cloud

> ⚠️ Ollama cannot run on Streamlit Cloud. For cloud deployment, replace the `ollama.chat()` calls in `flight_agent.py` and `app.py` with a cloud-based LLM API (e.g., OpenAI, Groq, or Anthropic).

Steps for deployment:

1. Push your code to a public GitHub repository.
2. Go to [https://streamlit.io/cloud](https://streamlit.io/cloud) and connect your repo.
3. Set `SERPAPI_KEY` in **App Settings → Secrets**.
4. Deploy.

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| `ollama: connection refused` | Run `ollama serve` in a terminal first |
| `Missing API Key` error | Enter your SerpApi key in the sidebar and click **Set Key** |
| `No flights found` | Try adjusting the date or use IATA codes directly (e.g., HAN → SGN) |
| JSON parse error from LLaMA | Restart Ollama or retry the query |
| City not recognized | Use the 3-letter IATA code instead (e.g., "DAD" for Da Nang) |

---

## 📁 Project Structure

```
ai-flight-agent/
├── app.py              # Streamlit UI and chat logic
├── flight_agent.py     # Flight search, IATA lookup, AI extraction
├── .env                # Local API key (not committed to git)
└── README.md
```

---

## 📄 License

MIT License. Free to use and modify.
