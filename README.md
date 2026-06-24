# NegotiBot AI — Negotiation Agent

**An autonomous buyer-side agent that scrapes a marketplace listing, then chats with the seller and haggles the price down for you.**

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) ![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat&logo=langchain&logoColor=white) ![Google Gemini](https://img.shields.io/badge/Gemini-8E75B2?style=flat&logo=googlegemini&logoColor=white) ![React](https://img.shields.io/badge/React_18-20232A?style=flat&logo=react&logoColor=61DAFB) ![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat&logo=vite&logoColor=white) ![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat&logo=tailwindcss&logoColor=white) ![WebSockets](https://img.shields.io/badge/WebSockets-010101?style=flat&logo=socketdotio&logoColor=white)

## Overview

NegotiBot AI is a marketplace negotiation agent. You give it a product URL (OLX, Quikr, or Facebook Marketplace), a target price, and a maximum budget in INR. It scrapes the listing, opens a chat with the seller, and runs a multi-round negotiation on your behalf — picking an opening offer, reading the seller's replies, switching tactics as the conversation moves, and either closing a deal or walking away when it makes sense to.

The point is to take the tedious part of buying second-hand off your plate. Finding a listing is easy; the back-and-forth messaging ("can you do less?", "what's your final price?", "I have another buyer") is the slow part, and it's also where most people leave money on the table. NegotiBot models that conversation as a state machine with named negotiation tactics and a decision engine that decides when to push, when to concede, and when to stop.

It was built for a September 2025 hackathon (the `Version 1/` folder still carries the problem statement PDFs and the pitch deck) and then grown into a larger second version with authentication, dual buyer/seller portals, and a LangChain-driven agent. The backend is FastAPI; the main app is `version 2.0.0` ("NegotiBot AI - Full Implementation"). It is a working prototype, not a production deployment.

## Key Features

- **URL-to-negotiation flow** — paste an OLX / Quikr / Facebook Marketplace product URL, set target price + max budget + an approach, and the agent handles discovery and bargaining end to end.
- **Negotiation state machine** — every conversation moves through five phases: `OPENING → EXPLORATION → BARGAINING → CLOSING → DEADLOCK`, with phase chosen from message count and detected price/closing keywords.
- **Eight named tactics** — Anchoring, Scarcity, Bundling, Reciprocity, Authority, Social Proof, Commitment, and Urgency, each with a configurable weight in `.env`.
- **Seller-personality modeling** — the agent classifies the seller as flexible, firm, eager, hesitant, or aggressive and adapts how hard it pushes.
- **Sentiment and flexibility analysis** — a `ConversationAnalyzer` scores each seller message for tone and willingness to move on price before a response is chosen.
- **LangChain agent with custom tools** — a Gemini-backed agent equipped with `market_analysis`, `price_calculator`, and `negotiation_strategy` tools, plus conversation-buffer memory.
- **Dual LLM providers with fallback** — OpenAI GPT as the default provider, Gemini Pro as the fallback, and a keyword-based static responder so the chat keeps working when no API key is present.
- **Three negotiation approaches** — assertive, diplomatic, or considerate, picked per session and reflected in the agent's tone.
- **Real-time chat over WebSockets** — separate `/ws/user/{session_id}` and `/ws/seller/{session_id}` channels stream messages, typing indicators, and status updates live.
- **Buyer and seller portals** — a buyer dashboard to start and watch negotiations, and a seller portal to play the other side and test the agent.
- **JWT authentication with roles** — register/login as a `buyer` or `seller`, with bcrypt password hashing and session validation.
- **Market analysis** — compares the listing against a suggested price range and competitive prices to inform the opening offer.
- **Confidence-based decisions** — accept / counter / walk-away calls are driven by a confidence score and configurable thresholds (`MIN_CONFIDENCE_THRESHOLD`, `HANDOFF_TRIGGER_THRESHOLD`).
- **Web scraping with fallbacks** — Playwright / Selenium / BeautifulSoup / cloudscraper with retry logic, per-platform extractors, and URL-based fallback when a page can't be parsed.
- **JSON-file persistence** — sessions, users, products, and negotiation context are stored as JSON (no external DB required to run).

## How It Works

The system is two halves: a FastAPI backend that runs the agent, and a React/Vite frontend (plus standalone HTML portals) that drives it.

### 1. Scrape the listing

`scraper_service.py` (the largest single module, ~71 KB) takes the product URL, detects the platform from the domain, and routes to the matching extractor — `_scrape_olx`, `_scrape_quikr`, or `_scrape_facebook`. Each pulls title, price, description, seller, location, images, features, and posted date, with retry attempts and timeouts. When live extraction fails, it falls back to deriving a title from the URL so a session can still start. `enhanced_scraper.py` adds a hardened path on top of the base service. Scraped data is normalized into the `Product` Pydantic model (price + `original_price`, platform, condition, contact, etc.).

### 2. Read the seller, pick a phase

For each incoming seller message, `negotiation_engine.py` runs a five-step turn:

1. `ConversationAnalyzer` scores the message for sentiment (positive/negative/neutral keyword sets) and flexibility (e.g. "negotiate", "flexible" vs "firm", "final", "non-negotiable").
2. The engine picks the current `NegotiationPhase` from message count plus closing/price signals — for example, six-plus messages with a flexibility score under 0.2 is treated as a `DEADLOCK`.
3. `DecisionEngine` makes the strategic call (push, concede, accept, pause, walk away) and attaches a confidence value.
4. `StrategySelector` chooses which of the eight tactics to apply for this turn, weighted by the `.env` config.
5. `ResponseGenerator` produces the actual reply text.

### 3. The LLM agent

`langchain_agent.py` wraps the above in a LangChain agent built on `ChatGoogleGenerativeAI` (Gemini) with `ConversationBufferMemory`. It exposes three custom `BaseTool`s the agent can call:

- **`market_analysis`** — returns a suggested price range and competitive prices around the listing price.
- **`price_calculator`** — a progressive offer strategy: aggressive early rounds, middle-ground mid-negotiation, and final offers near budget late, always clamped between target price and max budget.
- **`negotiation_strategy`** — decides which tactics fit the latest seller message.

`gemini_service.py` and `enhanced_ai_service.py` handle direct model calls, provider selection, retries, and the offline keyword-based fallback responder, so the chat degrades gracefully instead of breaking when the LLM is unreachable.

### 4. Context and sessions

`mcp_integration.py` implements a Model Context Protocol layer — a `NegotiationContext` dataclass that bundles product info, buyer/seller profiles, market data, conversation history, current phase, sentiment, price history, and success metrics, persisted via a JSON context manager. `session_manager.py` (~37 KB) tracks the lifecycle of each negotiation, and `database.py` provides the JSON-file store used across the app.

### 5. Real-time delivery

`main.py` (~56 KB, FastAPI) ties it together. It serves the portals, exposes the REST API, and runs two WebSocket endpoints — one for the buyer side and one for the seller side — that push messages, typing indicators, and status changes as the negotiation runs. `websocket_manager.py` handles the connection pool, heartbeats, and broadcast.

### 6. Frontend

The React 18 app (Vite) lives in `frontend/src` with components for the chat interface, message bubbles, product cards, market-analysis panel, sidebar, and a full seller portal. State is held in Zustand (`useNegotiationStore`), API and socket calls go through `services/api.js` and `services/websocket.js`, and the UI uses Tailwind CSS, Framer Motion, Headless UI, and Lucide icons. There are also standalone `react-app.html` and `seller-portal.html` builds, plus the original hackathon demo under `Version 1/demo/`.

## Results / Highlights

- **8 negotiation tactics** and a **5-phase** negotiation state machine, with **5 seller personality** profiles driving how the agent adapts.
- **3 marketplace scrapers** (OLX, Quikr, Facebook Marketplace) with multi-engine fallback (Playwright / Selenium / BeautifulSoup / cloudscraper).
- **Dual LLM providers** (OpenAI default, Gemini Pro fallback) plus an offline static responder — three layers before the chat fails.
- Default config runs up to **10 negotiation rounds**, opens at **70%** of the reference price, and uses tactic weights from 0.5 to 0.8.
- The backend spans **~12 Python modules** (~440 KB of Python), the largest being the scraper (~71 KB), main app (~56 KB), and LangChain agent (~37 KB).
- The hackathon pitch deck framed it as "the first autonomous buyer-side negotiation agent" and claimed roughly **25–30% average savings** in demos — a project claim, not an independently measured benchmark.

## Tech Stack

- **Languages:** Python, JavaScript (JSX), HTML, CSS
- **Backend / API:** FastAPI, Uvicorn, Pydantic, WebSockets, PyJWT / python-jose, bcrypt
- **AI / agent:** LangChain (community, core, google-genai, experimental), Google Gemini Pro, OpenAI GPT, LangSmith, Model Context Protocol (MCP)
- **Scraping:** Playwright, Selenium, BeautifulSoup, lxml, cloudscraper, fake-useragent, requests-html, httpx / aiohttp
- **Data:** Pandas, NumPy, JSON-file storage (sessions / users / products / contexts)
- **Frontend:** React 18, Vite, Tailwind CSS, Zustand, Framer Motion, Headless UI, Lucide React, React Hook Form, React Hot Toast
- **Config / infra:** python-dotenv, tenacity (retries); optional hooks for Redis / SQLite / Prometheus in `.env` (off by default)

## Getting Started

### Prerequisites
- Python 3.10+ (the code notes Python 3.13 compatibility tweaks)
- Node.js 18+ and npm
- A Gemini and/or OpenAI API key (optional — the chat falls back to a static responder without one)

### Installation
```bash
git clone https://github.com/DCode-v05/Negotiation-Agent.git
cd Negotiation-Agent

# Backend
cd backend
python -m venv venv
source venv/bin/activate          # Windows: .\venv\Scripts\activate
pip install -r ../requirements.txt
playwright install                # browser binaries for scraping

# copy the env template (from repo root) and add your keys
cp ../.env.example .env
```

Set at least `GEMINI_API_KEY` or `OPENAI_API_KEY` in `.env` (plus `SECRET_KEY` for auth). Provider order, tactic weights, max rounds, and scraping behavior are all configurable there.

### Running
```bash
# Backend (from backend/) — serves API + portals on port 8001 by default
uvicorn main:app --reload --port 8001

# Frontend (in a second terminal, from frontend/)
cd frontend
npm install
npm run dev
```

Backend API docs: `http://localhost:8001/docs` · Frontend: `http://localhost:5173`

## Usage

1. Open the frontend and register or log in as a **buyer** (or **seller** to test the other side).
2. Start a negotiation: paste a product URL (OLX / Quikr / Facebook Marketplace), set your **target price** and **max budget** in INR, pick an **approach** (assertive / diplomatic / considerate) and a **timeline** (urgent / week / flexible).
3. The agent scrapes the listing, runs a market analysis, and opens the chat. Watch rounds stream in over WebSocket — each shows the tactic used, the phase, and a confidence score.
4. Use the **seller portal** to reply as the seller and see how the agent reacts, or let it run against a real listing.
5. The session ends in success (a deal), a walk-away, or a handoff when confidence drops below threshold. Final price and outcome are saved to the session.

For a quick try without scraping, the API also exposes `/api/demo-negotiate` and `/api/market-analysis` endpoints.

## Project Structure

```
Negotiation-Agent/
├── backend/
│   ├── main.py                 # FastAPI app: REST + WebSocket endpoints, portals
│   ├── negotiation_engine.py   # 5-phase state machine, 8 tactics, decision/strategy/analyzer
│   ├── langchain_agent.py      # LangChain agent + custom market/price/strategy tools
│   ├── gemini_service.py       # Gemini calls + offline keyword fallback responder
│   ├── enhanced_ai_service.py  # Provider selection, retries, advanced AI path
│   ├── mcp_integration.py      # Model Context Protocol context manager
│   ├── scraper_service.py      # OLX / Quikr / Facebook extractors with fallbacks
│   ├── enhanced_scraper.py     # Hardened scraping path
│   ├── session_manager.py      # Negotiation session lifecycle
│   ├── auth_service.py         # JWT auth, bcrypt, buyer/seller roles
│   ├── websocket_manager.py    # Connection pool, heartbeats, broadcast
│   ├── database.py             # JSON-file store
│   ├── models.py               # Pydantic models (Product, Session, ChatMessage, ...)
│   └── data/                   # users / sessions / products JSON
├── frontend/
│   ├── src/
│   │   ├── components/         # ChatInterface, SellerPortal, MarketAnalysis, Sidebar, ...
│   │   ├── services/           # api.js, websocket.js
│   │   ├── hooks/              # useNegotiationStore (Zustand)
│   │   └── App.jsx / main.jsx
│   ├── react-app.html          # standalone React build
│   ├── seller-portal.html      # standalone seller portal
│   ├── package.json            # React 18, Vite, Tailwind, Zustand, Framer Motion
│   └── vite.config.js
├── Version 1/                  # original hackathon build + demo + pitch deck / problem PDFs
├── data/                       # general JSON data
├── .env.example               # full config template (keys, tactics, scraping, thresholds)
└── requirements.txt           # Python dependencies
```

---

## Contact

**Portfolio:** [Denistan](https://www.denistan.me)<br>
**LinkedIn:** [Denistan](https://www.linkedin.com/in/denistanb)<br>
**GitHub:** [DCode-v05](https://github.com/DCode-v05)<br>
**LeetCode:** [Denistan_B](https://leetcode.com/u/Denistan_B)<br>
**Email:** [denistanb05@gmail.com](mailto:denistanb05@gmail.com)

Made with ❤️ by **Denistan B**
