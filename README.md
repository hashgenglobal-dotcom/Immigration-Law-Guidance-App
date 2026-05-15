# Immigration Law Guidance App

**HashGen Global LLC** - AI-Powered Legal Information Assistant  
**Version:** 0.1.0 (MVP Development)  
**Created:** May 14, 2026

---

## 🎯 Mission

Provide accurate, citation-backed immigration law information to immigrants in the U.S. — **never from AI memory, only from retrieved official sources** (USCIS, eCFR, INA, BIA).

**Safety First:** This is legal *information*, not legal *advice*. All outputs include disclaimers and high-risk case referrals to attorneys.

---

## 📋 MVP Scope

**20 Common Questions** mapped to official legal sources:

1. Can I work while my asylum case is pending?
2. What happens if I overstay my visa?
3. Can I apply for asylum after one year?
4. What is adjustment of status?
5. Can I apply for citizenship after getting a green card?
6. What documents do I need for naturalization?
7. What is unlawful presence?
8. What happens if I receive a Notice to Appear?
9. Can I travel while my green card application is pending?
10. What is advance parole?
11. What is a work permit?
12. Can an F-1 student work?
13. What happens if my visa expires?
14. What is deportability?
15. What is inadmissibility?
16. Can I sponsor my spouse?
17. What is public charge?
18. What should I do if ICE comes to my door?
19. What is TPS?
20. How do I check my USCIS case status?

**Source Mapping:** [`docs/01-mvp-questions-source-mapping.md`](docs/01-mvp-questions-source-mapping.md)

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   React/Next.js │────▶│  FastAPI Backend │────▶│   PostgreSQL 18 │
│   Frontend      │     │  (Python 3.13)   │     │   + pgvector    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │   Ollama (Local) │
                        │   - nomic-embed  │
                        │   - llama3.1     │
                        └──────────────────┘
```

**Key Design Principles:**
- **Retrieval-Augmented Generation (RAG):** AI answers only from retrieved PostgreSQL chunks
- **Dataset Versioning:** Users query stable, published datasets (no partial updates)
- **Hybrid Search:** Vector (HNSW) + keyword (PostgreSQL full-text) retrieval
- **Local-First:** All AI processing on-device (no public API calls for user data)
- **Privacy-Safe Audit Trail:** Privacy-safe audit metadata is logged (hashes, citations used, retrieved chunk IDs, risk level, refusal flag, latency), but full user questions and full generated answers are **not stored by default**.

---

## 🛠️ Tech Stack

| Layer | Tool | Version |
|-------|------|---------|
| **Frontend** | React + Next.js | 19.2.x + 16.2.x |
| **Frontend Build** | Vite | 8.0.x |
| **Language** | TypeScript / Python | 6.0.x / 3.13.x |
| **Styling** | Tailwind CSS | 4.3.x |
| **Backend API** | FastAPI | 0.136.x |
| **ASGI Server** | Uvicorn | 0.46.x |
| **Data Validation** | Pydantic | 2.13.x |
| **ORM** | SQLAlchemy | 2.0.x |
| **DB Migrations** | Alembic | 1.18.x |
| **Database** | PostgreSQL | 18.x |
| **Vector Extension** | pgvector | 0.8.2 |
| **Queue/Cache** | Redis | 8.x |
| **Background Jobs** | RQ | Current stable |
| **Embeddings** | Ollama (nomic-embed-text) | 0.23.x |
| **LLM** | Ollama (llama3.1:8b) | 0.23.x |
| **Containerization** | Docker | Current |

**Full details:** [`docs/TECH_STACK.md`](docs/TECH_STACK.md)

---

## 📦 Project Structure

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
│   └── TECH_STACK.md
├── scripts/
│   └── test-ollama-embeddings.py
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites

```bash
# Install core tools (macOS)
brew install git node uv postgresql@18 pgvector redis ollama docker

# Start services
brew services start postgresql@18
brew services start redis
brew services start ollama
```

### Database Setup

```bash
# Create database
createdb immigration_law_dev

# Enable pgvector
psql -d immigration_law_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify
psql -d immigration_law_dev -c "\dx vector"
```

### Ollama Models

```bash
# Pull embedding model (768 dimensions)
ollama pull nomic-embed-text

# Pull LLM for answer generation
ollama pull llama3.1:8b
```

### Backend Setup

```bash
cd backend

# Create virtual environment with uv
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Verify Installation

```bash
# Test Ollama embeddings
python scripts/test-ollama-embeddings.py

# Test PostgreSQL + pgvector
psql -d immigration_law_dev -c "SELECT '[1,2,3]'::vector(3);"

# Test Redis
redis-cli ping  # Should return: PONG

# Test backend API
curl http://localhost:8000/api/health
```

---

## 📊 Database Schema

**10 Tables:**

| Table | Purpose |
|-------|---------|
| `source_registry` | Track 6 official legal sources |
| `raw_documents` | Audit trail with content hashing |
| `legal_documents` | Cleaned metadata |
| `legal_sections` | Specific sections (e.g., 8 CFR § 208.7) |
| `legal_chunks` | **Retrieval-ready with embeddings + full-text** |
| `scenario_guides` | User-friendly guides (ICE, overstay, etc.) |
| `dataset_versions` | Version control (only 1 active at a time) |
| `ingestion_jobs` | Track admin update jobs |
| `privacy_safe_answer_logs` | Privacy-safe metadata audit (hashes, citations used, chunk IDs, risk level, refusal flag, latency) — **no full questions or answers stored** |
| `admin_users` | Dashboard auth |

**Schema SQL:** [`database/migrations/001-initial-schema.sql`](database/migrations/001-initial-schema.sql)

---

## 🛡️ Privacy Rule

This app handles sensitive immigration-related questions (asylum facts, visa overstay, ICE encounters, family details, criminal history, removal proceedings, etc.). The following rules are mandatory:

- **Real user questions are processed locally/private.** No user query is sent to any public AI API.
- **Full question text and answer text are not stored by default.** The backend must not persist raw user questions or raw generated answers.
- **Only privacy-safe metadata may be stored** — for example: question hash, answer hash, citations used, retrieved chunk IDs, risk level, refusal flag, model name, embedding model, language, and latency. This metadata lives in the `privacy_safe_answer_logs` table.
- **Public legal-source data is safe to store and share.** USCIS / eCFR / INA / BIA / Federal Register text, citations, chunks, and embeddings of public legal content may be stored in the database and committed to the repo (via migrations and seed scripts).
- **Private user data must never be committed to GitHub.** This includes `.env` files, real user questions, immigration case facts, chat logs, uploaded user documents, local database dumps, addresses, A-numbers, passport numbers, and any other personally identifying or case-identifying information.

## 🔒 Data Security (HashGen Protocol 2)

**Zero tolerance for exposing client data to public APIs.**

- ✅ All embeddings generated locally via Ollama
- ✅ All LLM inference runs locally (Ollama/vLLM)
- ✅ No user questions sent to OpenAI, Anthropic, etc.
- ✅ PostgreSQL database on local machine or private VPC
- ✅ Redis for caching (local or private network only)
- ✅ No full user questions or full answers persisted — only privacy-safe metadata in `privacy_safe_answer_logs`

---

## 🧪 Development Workflow

### Team Coordination

- **Hash:** CEO/Founder, product direction, legal source mapping
- **Rishi Raj:** DEV partner, backend/frontend implementation
- **Git:** All work pushed to `https://github.com/hashgenglobal-dotcom/Immigration-Law-Guidance-App`

### Branch Strategy

```bash
# Main branch (production-ready)
git checkout main

# Feature branches
git checkout -b feature/ecfr-ingestion
git checkout -b feature/retrieval-endpoint
git checkout -b frontend/chat-ui
```

### Commit Convention

```bash
# Format: <type>(<scope>): <description>
git commit -m "feat(ingestion): add eCFR Title 8 XML parser"
git commit -m "fix(retrieval): handle empty search results"
git commit -m "docs: update MVP question mapping"
```

---

## 📅 Development Phases

### Phase 0: Planning ✅ COMPLETE
- [x] 20 MVP questions defined
- [x] Source mapping document created
- [x] Database schema designed
- [x] Tech stack finalized

### Phase 1: Database Foundation ✅ COMPLETE
- [x] PostgreSQL 18 + pgvector 0.8.2 installed
- [x] Database schema created (10 tables)
- [x] Source registry seeded (6 official sources)

### Phase 2: eCFR Ingestion Pipeline (IN PROGRESS)
- [ ] Build eCFR Title 8 XML fetcher
- [ ] Parse sections (8 CFR § 208.7, 208.4, 245.1-245.2, etc.)
- [ ] Chunk text (500-1000 tokens, 50-100 overlap)
- [ ] Generate embeddings (Ollama + nomic-embed-text)
- [ ] Store in PostgreSQL with versioning
- [ ] Create first active dataset

### Phase 3: Retrieval MVP
- [ ] Build FastAPI backend skeleton
- [ ] Implement `POST /api/chat/ask` endpoint
- [ ] Hybrid search function (vector + keyword)
- [ ] LLM answer generation with citations
- [ ] Test against 5 of 20 MVP questions

### Phase 4: USCIS Policy Manual Ingestion
- [ ] Scrape USCIS Policy Manual volumes
- [ ] Parse chapters mapped to MVP questions
- [ ] Ingest into database

### Phase 5: INA/U.S. Code Ingestion
- [ ] Fetch Title 8 U.S. Code sections
- [ ] Parse INA statutes
- [ ] Link to CFR sections

### Phase 6: Safety Layer
- [ ] Implement risk-level detection
- [ ] Mandatory disclaimers on all outputs
- [ ] Attorney referral logic for high-risk cases

### Phase 7: Admin Dashboard
- [ ] Build React admin interface
- [ ] Source management (add/update/archive)
- [ ] Ingestion job monitoring
- [ ] Dataset version management

### Phase 8: Frontend Chat UI
- [ ] Build React chat interface
- [ ] Question suggestions (20 MVP questions)
- [ ] Citation display
- [ ] Disclaimer rendering

### Phase 9: Testing & QA
- [ ] Unit tests (pytest)
- [ ] Integration tests (API endpoints)
- [ ] E2E tests (Playwright)
- [ ] Security audit

### Phase 10: Deployment
- [ ] Docker Compose for local dev
- [ ] Production Docker images
- [ ] Deploy to Render/Railway/AWS
- [ ] Monitoring + logging setup

---

## 📝 Key Documents

- **MVP Questions + Source Mapping:** [`docs/01-mvp-questions-source-mapping.md`](docs/01-mvp-questions-source-mapping.md)
- **Tech Stack:** [`docs/TECH_STACK.md`](docs/TECH_STACK.md)
- **Database Setup:** [`database/SETUP_COMPLETE.md`](database/SETUP_COMPLETE.md)
- **Schema SQL:** [`database/migrations/001-initial-schema.sql`](database/migrations/001-initial-schema.sql)
- **eCFR Title 8 — First Ingestion Milestone Plan:** [`docs/ecfr-ingestion-milestone-plan.md`](docs/ecfr-ingestion-milestone-plan.md)
- **Local Embeddings Milestone Plan:** [`docs/local-embeddings-milestone-plan.md`](docs/local-embeddings-milestone-plan.md)
- **Dataset Activation Milestone Plan:** [`docs/dataset-activation-milestone-plan.md`](docs/dataset-activation-milestone-plan.md)

---

## 🤝 Contributing

**Team Members:**
- Hash (@hashgenglobal) - Product, Legal Sources
- Rishi Raj - Backend/Frontend Development

**Workflow:**
1. Create feature branch from `main`
2. Implement + test locally
3. Push to GitHub
4. PR for review (if applicable)
5. Merge to `main`

---

## 📄 License

Proprietary - HashGen Global LLC  
**EIN:** 41-4374777  
**Address:** 30 N Gould St, Ste R, Sheridan, WY, 82801 USA

---

## 🦅 Contact

**Hashish Gyajangi (Hash)**  
CEO/Founder @ HashGen Global  
PhD Candidate (IT/AI)  
Email: hash@hashgen.global
