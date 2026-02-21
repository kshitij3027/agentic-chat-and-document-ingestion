# Agentic Chat and Document Ingestion

A RAG application with two interfaces: **Chat** (default view) for threaded conversations with retrieval-augmented responses, and **Ingestion** for manual file upload, processing tracking, and document management. Configuration is via environment variables; there is no admin UI. Files are uploaded manually via drag-and-drop only—no connectors or automated pipelines.

## Stack

| Layer      | Choice |
| ---------- | ------ |
| Frontend   | React + TypeScript + Vite + Tailwind + shadcn/ui |
| Backend    | Python + FastAPI |
| Database   | Supabase (Postgres, pgvector, Auth, Storage, Realtime) |
| LLM        | OpenAI / OpenRouter |
| Observability | LangSmith |

## Project structure

```
agentic-rag-starter/
├── backend/
│   ├── app/                 # FastAPI app, routers, services
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/                 # React app, pages, components
│   ├── package.json
│   └── .env.example
├── CLAUDE.md                 # AI coding instructions
├── PRD.md                    # Product requirements
└── IMPLEMENTATION_GUIDE.md   # Implementation reference
```

## Prerequisites

- **Node.js** 20+
- **Python** 3.11+
- A **Supabase** project (Postgres, Auth, Storage, Realtime)
- **OpenAI** and/or **OpenRouter** API keys as needed

## Local run

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Edit .env with your Supabase and API keys
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm ci
cp .env.example .env       # Edit .env with Supabase URL, anon key, API URL
npm run dev
```

Frontend dev server runs at `http://localhost:5173` (or the port Vite reports). Point it at the backend (e.g. `http://localhost:8000`) via your frontend env config.

## Configuration

- **Backend:** Copy `backend/.env.example` to `backend/.env` and set Supabase URL, service role key, and LLM/embedding keys as required.
- **Frontend:** Copy `frontend/.env.example` to `frontend/.env` and set Supabase URL, anon key, and backend API URL.

Do not commit `.env` files or secrets.

## Further reading

- [PRD.md](PRD.md) — Product requirements and module overview.
- [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) — Architecture and implementation details.

This starter is based on the Agentic RAG Masterclass.
