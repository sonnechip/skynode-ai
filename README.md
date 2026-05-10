# ✈️ SkyNode AI

AI-powered flight planning assistant built with Streamlit, Ollama (LLaMA 3), and SerpApi.  
Optimized for intelligent travel search, multilingual interaction, and AMD AI acceleration.

---

# Table of Contents

- Features
- Tech Stack
- Installation
- Configuration
- Running the App
- How to Use
- Project Structure
- Contribution Guidelines
- Pull Request Process
- Security
- License

---

# Features

- Natural language flight search
- Multi-language support
- One-way & round-trip flights
- Flight comparison and optimization
- Best-flight recommendation
- Session analytics
- Privacy-focused local AI processing

---

# Tech Stack

| Category | Technology |
|---|---|
| Frontend | Streamlit |
| AI Model | Ollama + LLaMA 3 |
| Flight Data | SerpApi |
| Language | Python |
| Environment | dotenv |
| Hardware Optimization | AMD Ryzen AI |

---

# 🚀 Installation

## 1. Clone Repository

```bash
git clone https://github.com/your-username/skynode-ai.git

cd skynode-ai
```

---

## 2. Install Dependencies

```bash
pip install streamlit ollama google-search-results python-dotenv
```

---

## 3. Install Ollama

Download Ollama:

https://ollama.com

Pull the LLaMA 3 model:

```bash
ollama pull llama3
```

Start Ollama:

```bash
ollama serve
```

---

# Configuration

Create a `.env` file:

```env
SERPAPI_KEY=your_key_here
```

Get your API key from:

https://serpapi.com

---

# Running the App

```bash
streamlit run app.py
```

Open:

```bash
http://localhost:8501
```

---

# Example Queries

## English

```text
Find me a flight from Hanoi to Singapore on 2026-08-15
```

## Vietnamese

```text
Tìm vé máy bay từ Hà Nội đến Bangkok ngày 20 tháng 7 năm 2026
```

## Round Trip

```text
Book a round trip from Ho Chi Minh to Tokyo, depart July 10, return July 20
```

---

# Project Structure

```text
skynode-ai/
├── app.py
├── flight_agent.py
├── hardware/
├── .env
├── README.md
```

---

# Contribution Guidelines

We use a Feature Branch Workflow.

| Branch | Purpose |
|---|---|
| `main` | Production-ready |
| `dev` | Integration branch |
| `feature/[name]-[task]` | Personal feature branch |

Example:

```bash
feature/minh-dashboard
```

---

## Development Workflow

1. Pull latest changes
2. Create feature branch
3. Commit locally
4. Push to GitHub
5. Open Pull Request to `dev`

> Never push directly to `main` or `dev`

---

# Commit Convention

Format:

```bash
type(scope): description
```

Examples:

```bash
feat(agent): add multilingual extraction
fix(parser): fix outbound date parsing
docs: update README
```

---

# Pull Request Process

- No direct commits to `main`
- Remove debug logs before PR
- Avoid hardcoded credentials
- At least one teammate reviews major changes
- Use Squash and Merge

---

# Coding Standards

- Follow PEP 8
- Use meaningful variable names
- Keep modules isolated
- Notify teammates before changing shared data contracts

---

# Security

- Store secrets in `.env`
- Never upload API keys
- Do not commit sensitive user data

---

# AMD Optimization

When implementing AMD acceleration:
- Document optimization steps in `hardware/`
- Include benchmark results if possible
- Prefer lightweight inference pipelines

---
