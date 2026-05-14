# Immigration Law Guidance App - Tech Stack

**Last Updated:** 2026-05-14  
**Project:** HashGen Global LLC - Immigration Law Information Assistant

---

## 17. Recommended MVP Stack (With Versions)

### Frontend

| Layer | Tool | Version | Notes |
|-------|------|---------|-------|
| **Frontend Web** | React | 19.2.x | Latest stable |
| **Framework Option** | Next.js | 16.2.x | SSR/SSG support |
| **Mobile Option** | React Native | 0.85.x | iOS/Android |
| **Build Tool** | Vite | 8.0.x | Fast HMR, tree-shaking |
| **Language** | TypeScript | 6.0.x | Type safety |
| **Styling** | Tailwind CSS | 4.3.x | Utility-first CSS |

### Backend

| Layer | Tool | Version | Notes |
|-------|------|---------|-------|
| **Language** | Python | 3.13.x | Recommended |
| **API Framework** | FastAPI | 0.136.x | Async, OpenAPI auto-docs |
| **ASGI Server** | Uvicorn | 0.46.x | Production-ready |
| **Data Validation** | Pydantic | 2.13.x | V2 stable |
| **ORM** | SQLAlchemy | 2.0.x | Async support |
| **DB Migrations** | Alembic | 1.18.x | SQLAlchemy companion |

### Database

| Layer | Tool | Version | Notes |
|-------|------|---------|-------|
| **Database** | PostgreSQL | 17.x / 18.x | Latest LTS |
| **Vector Extension** | pgvector | 0.8.x | HNSW + IVFFlat indexes |
| **Queue/Cache** | Redis | 8.x | Background jobs |
| **Background Jobs** | RQ or Celery | Current stable | RQ simpler for MVP |

### AI/ML Layer

| Layer | Tool | Version | Notes |
|-------|------|---------|-------|
| **Local Embedding Runtime** | Sentence Transformers / Ollama | Current stable | |
| **Vector/Embedding Library** | sentence-transformers | 5.5.x | HuggingFace |
| **Local LLM Runtime (MVP)** | Ollama | 0.23.x+ | Simple setup |
| **Local LLM Serving (Production)** | vLLM | 0.20.x | High-throughput |

### DevOps & Deployment

| Layer | Tool | Version | Notes |
|-------|------|---------|-------|
| **Version Control** | GitHub | Current | |
| **Containerization** | Docker | Current stable | |
| **Deployment** | AWS / Azure / Private VM / Render / Railway | Based on budget | |

---

## Version Sources (As of May 14, 2026)

- **React:** 19.2.x (official docs)
- **FastAPI:** 0.136.1 (PyPI)
- **Node.js:** 24.15.0 LTS / 26.1.0 latest (nodejs.org)
- **PostgreSQL:** 18.4, 17.10, 16.14, 15.18, 14.23 (announced May 14, 2026)
- **pgvector:** 0.8.2 (February 2026, security fix included)
- **Vite:** 8.0.x (npm)
- **React Native:** 0.85.x (official docs)
- **Next.js:** 16.2.6 (official docs)
- **Tailwind CSS:** 4.3.0 (GitHub releases)
- **vLLM:** 0.20.2 (PyPI)
- **sentence-transformers:** 5.5.0 (PyPI)
- **Ollama:** 0.23.x (GitHub)

---

## HashGen-Specific Configuration

### Data Security (Protocol 2)
**Requirement:** Zero tolerance for exposing client data to public APIs

**Implementation:**
- **Embeddings:** Local via Ollama (`nomic-embed-text` or `mxbai-embed-large`)
- **LLM:** Local via Ollama (`llama3.1:8b` or `qwen2.5:7b` for MVP)
- **Production:** vLLM with quantized models (GGUF/GPTQ)
- **No public API calls** for user question processing

### Local-First Development Stack

```bash
# Python
python --version  # 3.13.x

# Ollama
ollama --version  # 0.23.x+
ollama pull nomic-embed-text
ollama pull llama3.1:8b

# PostgreSQL
psql --version  # 17.x or 18.x

# Redis
redis-server --version  # 8.x

# FastAPI dev server
uvicorn main:app --reload  # 0.46.x
```

### Production Deployment Stack

```yaml
# docker-compose.yml services
- postgres:17 (with pgvector 0.8.x)
- redis:8
- backend: Python 3.13 + FastAPI 0.136.x + vLLM 0.20.x
- frontend: Node 24.x + Next.js 16.2.x
```

---

## Repository Structure (Planned)

```
immigration-law-app/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── chat.py      # POST /api/chat/ask
│   │   │   │   ├── scenarios.py # GET /api/scenarios
│   │   │   │   └── admin.py     # Admin ingestion APIs
│   │   │   └── deps.py          # Dependencies (auth, DB session)
│   │   ├── core/
│   │   │   ├── config.py        # Settings (pydantic)
│   │   │   └── security.py      # JWT, password hashing
│   │   ├── db/
│   │   │   ├── base.py          # SQLAlchemy base
│   │   │   ├── session.py       # DB session factory
│   │   │   └── models.py        # SQLAlchemy models
│   │   ├── ingestion/
│   │   │   ├── sources/
│   │   │   │   ├── ecfr.py      # eCFR Title 8 fetcher
│   │   │   │   ├── uscis.py     # USCIS Policy Manual scraper
│   │   │   │   ├── uscode.py    # U.S. Code / INA fetcher
│   │   │   │   └── bia.py       # BIA decisions scraper
│   │   │   ├── chunking.py      # Text chunking logic
│   │   │   ├── embeddings.py    # Ollama embedding generation
│   │   │   └── pipeline.py      # Full ingestion orchestration
│   │   ├── retrieval/
│   │   │   ├── search.py        # Hybrid search (vector + keyword)
│   │   │   ├── rerank.py        # Reranking logic
│   │   │   └── llm.py           # Answer generation with citations
│   │   └── main.py              # FastAPI app entry
│   ├── alembic/
│   │   ├── versions/            # Migration files
│   │   └── env.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── lib/
│   ├── package.json
│   ├── tailwind.config.js
│   └── Dockerfile
├── database/
│   ├── migrations/
│   │   └── 001-initial-schema.sql
│   └── SETUP_COMPLETE.md
├── docs/
│   ├── 01-mvp-questions-source-mapping.md
│   └── TECH_STACK.md (this file)
├── docker-compose.yml
└── README.md
```

---

## Package Versions (requirements.txt - Planned)

```txt
# FastAPI & ASGI
fastapi==0.136.1
uvicorn[standard]==0.46.0
python-multipart==0.0.20

# Database
sqlalchemy==2.0.37
psycopg2-binary==2.9.10
alembic==1.18.0

# Validation
pydantic==2.13.0
pydantic-settings==2.10.0

# Background Jobs
rq==2.4.0
redis==6.4.0

# AI/ML
ollama==0.4.7
sentence-transformers==5.5.0

# Utilities
httpx==0.28.1
beautifulsoup4==4.13.4
lxml==6.0.0
python-dotenv==1.1.0
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.5.0

# Testing
pytest==8.4.0
pytest-asyncio==1.0.0
httpx==0.28.1
```

---

## Next Steps

1. **Initialize FastAPI backend** with Python 3.13
2. **Set up Ollama** with nomic-embed-text + llama3.1:8b
3. **Build eCFR ingestion pipeline** (Phase 2)
4. **Create retrieval endpoint** (Phase 3)
5. **Build React frontend** (Phase 9, after backend MVP)

---

## Current Status

- ✅ PostgreSQL 17.9 installed
- ✅ pgvector 0.8.2 installed
- ✅ Database schema created (10 tables)
- ✅ Source registry seeded (6 official sources)
- ⏳ FastAPI backend: Not started
- ⏳ eCFR ingestion: Not started
- ⏳ Ollama setup: Not started
