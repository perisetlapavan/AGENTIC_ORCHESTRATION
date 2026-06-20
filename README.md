# 🤖 Agentic Market Intelligence Suite

A multi-agent AI system that autonomously researches company competitors, generates Python visualization code, executes it, and self-corrects on failure — all orchestrated through a LangGraph state machine and served via a FastAPI backend.

![Market Chart Demo](market_chart.png)

---

## 🧠 What This Project Demonstrates

This project goes beyond simple LLM API calls. It implements a **production-style agentic loop** where:

- Agents have **specialized roles** (Researcher, Coder, Executor)
- A **Supervisor Router** dynamically decides which agent runs next
- The system **self-heals**: if generated code throws a runtime error, the loop routes back to the Coder with the error trace to auto-fix it
- Live web data is fetched via **Tavily Search** and injected into the LLM context before generating output

---

## 🏗️ System Architecture

```
User Input (Company Name)
        │
        ▼
┌─────────────────────────────────────────┐
│           LangGraph State Machine        │
│                                         │
│  ┌──────────┐    ┌────────┐    ┌──────────────┐  │
│  │Researcher│───▶│ Coder  │───▶│   Executor   │  │
│  │  Agent   │    │ Agent  │    │    Agent     │  │
│  └──────────┘    └────────┘    └──────┬───────┘  │
│       ▲               ▲               │           │
│       │    Supervisor Router          │ (on fail) │
│       └───────────────┴───────────────┘           │
└─────────────────────────────────────────┘
        │
        ▼
  FastAPI Backend  ←──→  HTML/JS Frontend
```

### Agent Roles

| Agent | Responsibility |
|---|---|
| **Researcher** | Queries Tavily web search, feeds live context to LLaMA 3.3 70B, extracts competitor names |
| **Coder** | Generates matplotlib Python code; receives error traces from failed runs for self-correction |
| **Executor** | Safely runs generated code, captures exceptions and routes them back to Coder |
| **Supervisor** | Conditional router evaluating shared state after every node — no hardcoded sequence |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | LLaMA 3.3 70B via Groq API (ultra-low latency inference) |
| **Agent Framework** | LangGraph (StateGraph with conditional edges) |
| **Web Search** | Tavily Search API (real-time web retrieval) |
| **Backend API** | FastAPI + Uvicorn |
| **Visualization** | Matplotlib (dynamically generated and executed) |
| **Frontend** | Vanilla HTML/JS + Tailwind CSS |

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/AGENTIC_ORCHESTRATION.git
cd AGENTIC_ORCHESTRATION
```

### 2. Set up a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
# Edit .env and add your API keys
```

You'll need:
- **Groq API key** → [console.groq.com/keys](https://console.groq.com/keys) (free tier available)
- **Tavily API key** → [app.tavily.com](https://app.tavily.com/) (free tier available)

### 5. Run the FastAPI backend
```bash
uvicorn main:app --reload --port 8000
```

### 6. Open the frontend
Open `index.html` directly in your browser, or serve it with:
```bash
python -m http.server 3000
```
Then visit `http://localhost:3000`.

---

## 📁 Project Structure

```
AGENTIC_ORCHESTRATION/
├── app.py              # Core LangGraph agent logic (Research → Code → Execute loop)
├── main.py             # FastAPI server — exposes REST endpoints
├── index.html          # Frontend UI — sends requests, displays chart
├── requirements.txt    # Python dependencies
├── .env.example        # Template for API keys (copy to .env)
├── .gitignore          # Excludes .env and generated files
└── README.md           # This file
```

---

## 🔄 Self-Correction Loop in Action

When the Executor agent catches a runtime error in generated code, it logs the traceback into the shared `MarketGraphState`. The Supervisor Router detects `execution_failed` and routes back to the Coder agent, passing the error message as context. The Coder regenerates fixed code. This loop runs until success or a max iteration limit.

```
[Coder] Generates matplotlib code
    ↓
[Executor] Runs code → NameError: 'plt' is not defined
    ↓
[Supervisor] Detects execution_failed → routes back to Coder
    ↓
[Coder] Receives error trace → fixes import → regenerates
    ↓
[Executor] Runs fixed code → ✅ Success
```

---

## 📡 API Reference

### `POST /api/v1/generate-chart`
Triggers the full agent workflow.

**Request body:**
```json
{ "company_name": "Tesla" }
```

**Response:**
```json
{
  "company_name": "Tesla",
  "competitors": ["BYD", "Rivian", "General Motors"],
  "chart_url": "/api/v1/charts/market_chart.png",
  "execution_status": "execution_success"
}
```

### `GET /api/v1/charts/{filename}`
Serves the generated chart image.

---

## 🔮 Potential Extensions

- [ ] Streaming agent logs to the frontend via SSE/WebSocket
- [ ] Dockerize the backend for one-command deployment
- [ ] Add Celery for async background task processing
- [ ] Persist results to a database (PostgreSQL/SQLite)
- [ ] Support multi-company comparison in a single run

---

## 👤 Author

**Perisetla Pavan Kalyan (Peaks)**  
AI Engineer & Data Scientist  
[LinkedIn](https://linkedin.com/in/YOUR_PROFILE) · [GitHub](https://github.com/YOUR_USERNAME)
