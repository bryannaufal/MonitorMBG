# 🍽️ MonitorMBG — Makan Bergizi Gratis Monitoring Dashboard

**Oversight Intelligence and Orchestration Layer** for government operators.

> DIGDAYA X HACKATHON 2026

---

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────────────┐
│  Next.js     │────▶│  FastAPI Backend                                 │
│  Dashboard   │ WS  │  ┌─────────┐ ┌───────────┐ ┌─────────────────┐ │
│  (Port 3000) │ SSE │  │ NLP     │ │ CV Engine │ │ Scoring Engine  │ │
│              │◀────│  │ Engine  │ │ + Nutrition│ │ + Cost Analysis │ │
└─────────────┘     │  └────┬────┘ └─────┬─────┘ └────────┬────────┘ │
                    │       │            │                  │          │
                    │  ┌────▼────────────▼──────────────────▼────┐     │
                    │  │          Celery Workers                 │     │
                    │  └────────────────┬───────────────────────┘     │
                    └──────────────────┼──────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │    Redis         │    PostgreSQL     │
                    │    (Broker)      │    (Database)     │
                    └──────────────────┴──────────────────┘
```

## 📂 Project Structure

```
MonitorMBG/
├── backend/          # Python FastAPI + Celery
│   ├── app/
│   │   ├── api/      # REST endpoints (versioned)
│   │   ├── models/   # SQLAlchemy ORM models
│   │   ├── schemas/  # Pydantic DTOs
│   │   ├── services/ # Business logic
│   │   │   ├── nlp_engine/   # IndoBERTweet, BERTopic
│   │   │   ├── cv_engine/    # Object detection, nutrition, hashing
│   │   │   ├── scoring/      # Severity, confidence, cost plausibility
│   │   │   └── copilot/      # RAG-based AI assistant
│   │   ├── workers/  # Celery async tasks
│   │   └── core/     # Database, auth, events
│   └── alembic/      # Database migrations
│
├── frontend/         # Next.js + TypeScript + TailwindCSS
│   └── src/
│       ├── app/           # App Router pages
│       ├── components/    # Dashboard, charts, copilot UI
│       ├── hooks/         # WebSocket, SSE, data fetching
│       ├── lib/           # API client, utilities
│       └── types/         # TypeScript type definitions
│
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose

### Option 1: Docker (Recommended)

```bash
# Clone and configure
cp .env.example .env

# Start all services
docker-compose up --build
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Option 2: Manual Setup

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

## 🔑 Core Modules

| Module | Description |
|--------|-------------|
| **Public Signal Intelligence** | Social media scraping + NLP (sentiment, topic clustering, anomaly detection) |
| **Multimodal Verification** | Image-text matching, perceptual hashing, OCR for document parsing |
| **Nutrition Estimation** | Food detection + portion estimation + calorie/macronutrient calculation |
| **Hybrid Scoring** | Severity scores, confidence levels, cost plausibility analysis |
| **AI Copilot** | RAG-based assistant for case synthesis and operator queries |

## 📄 License

This project is developed for the DIGDAYA X HACKATHON 2026.