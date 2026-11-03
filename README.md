# JobRadar

Personal tech job tracker. Discovers new jobs from company career pages and
public ATS APIs, filters them by your preferences, and sends Telegram alerts.

---

## Repo layout

```
jobradar/
├── AGENTS.md          – agent working rules (read at session start)
├── docs/PRD.md        – product requirements
├── .env.example       – environment variable template
├── web/               – Next.js 14 dashboard (TypeScript + Tailwind)
└── collectors/        – Python 3.11 collectors, migrations, Telegram
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Node.js | 18 LTS or 20 LTS |
| npm | 9+ |
| Python | 3.11+ |

---

## 1 — Environment variables

```bash
cp .env.example .env
# Edit .env and fill in DATABASE_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

---

## 2 — Web dashboard (`web/`)

```bash
cd web
npm install
npm run dev          # http://localhost:3000
```

`web/` reads `DATABASE_URL` from the environment (or `.env` in the repo root
when using a tool like `dotenv-cli`).

---

## 3 — Collectors (`collectors/`)

```bash
cd collectors

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install the package and dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint / format
ruff check .
ruff format .
```

`collectors/` reads `.env` from the repo root automatically via `conftest.py`
(using `python-dotenv`). Variables already set in the shell are never
overridden — in CI, use real environment variables and omit the `.env` file.

---

## Build plan

| Step | Goal |
|------|------|
| **0** | Repo layout, docs, env setup ✅ |
| 1 | Thin slice — real jobs from one Greenhouse company on a web page |
| 2 | Trustworthy data — dedupe, dates, source_runs, baseline run |
| 3 | Dashboard — filters, preferences, "new today" counts |
| **4** | Tracker — application statuses and notes ✅ |
| **5** | Alerts and automation — Telegram, GitHub Actions cron, Vercel deploy ✅ |
| 6 | More sources |

---

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for full deployment instructions covering Neon PostgreSQL, Vercel (`web/`), GitHub Actions scheduling, and Telegram Bot setup.

