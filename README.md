# HireIQ

An enterprise-grade AI hiring assistant that conducts structured candidate screening interviews, evaluates technical answers, and gives HR teams a dashboard to review results — all self-hosted, no third-party platforms.

---

## What it does

Candidates open a chat interface and are guided through a two-stage screening:

1. **Info gathering** — the AI collects name, email, phone, experience, role, location, and tech stack through natural conversation
2. **Technical interview** — 5 questions are generated dynamically based on the candidate's stated tech stack
3. **Scoring** — after the interview, Gemini evaluates each answer (1–5) with a written rationale

HR teams log into a private dashboard to browse completed interviews, view scores, and export data.

---

## Stack

| Layer | Technology |
|---|---|
| LLM | Google Gemini (`gemini-2.0-flash` / `gemini-1.5-pro`) |
| Backend | Python · FastAPI · Uvicorn |
| Frontend | React · Vite · TypeScript |
| Session store | Redis |
| Database | MongoDB (Motor async driver) |
| Auth | JWT (python-jose · bcrypt) |
| Streaming | Server-Sent Events (SSE) |
| Containers | Docker · docker-compose |
| Backend hosting | Railway |
| Frontend hosting | Vercel |
| CI/CD | GitHub Actions |

---

## Project structure

```
hireiq/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # interview, auth, dashboard routes
│   │   ├── core/           # interview engine, LLM service, validation
│   │   ├── db/             # MongoDB + Redis connection pools
│   │   ├── models/         # Pydantic schemas
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── pages/          # Interview (candidate) + Dashboard (HR)
│   │   ├── lib/            # API client + SSE streaming
│   │   ├── stores/         # Zustand state
│   │   └── styles/         # Design tokens + component CSS
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml       # Full local dev stack
├── .github/workflows/       # Deploy on push to main
├── BUILD_GUIDE.md           # Step-by-step implementation guide
└── .env.example             # Environment variable template
```

---

## Quick start (local)

**Prerequisites:** Docker Desktop, a Gemini API key, MongoDB Atlas URI

```bash
git clone https://github.com/arvinder004/hireIQ.git
cd hireIQ

cp .env.example .env
# Fill in GEMINI_API_KEY, MONGO_URI, JWT_SECRET_KEY

docker compose up --build
```

| Service | URL |
|---|---|
| Candidate chat | http://localhost:5173 |
| HR dashboard | http://localhost:5173/dashboard |
| API + docs | http://localhost:8000/docs |

---

## Environment variables

```bash
GEMINI_API_KEY      # https://aistudio.google.com/app/apikey
MONGO_URI           # MongoDB Atlas connection string
REDIS_URL           # redis://localhost:6379
JWT_SECRET_KEY      # python3 -c "import secrets; print(secrets.token_hex(32))"
FRONTEND_URL        # http://localhost:5173 (or Vercel URL in prod)
```

---

## Deployment

```bash
# Backend → Railway
cd backend && railway up

# Frontend → Vercel
cd frontend && vercel --prod
```

CI/CD via GitHub Actions automatically deploys on every push to `main`. See [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml).

---

## Build guide

The full step-by-step guide — covering every file, concept, and decision — is in [`BUILD_GUIDE.md`](BUILD_GUIDE.md).

---

## Author

**Arvinder Singh Dhoul**
