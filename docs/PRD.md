# JobRadar — PRD (MVP)

Personal tech job tracker. Discovers new jobs quickly, filters them by my preferences, and sends alerts so I don't have to search manually.

## 1. Goals

- Find new tech jobs from company career pages and public job feeds automatically.
- Show only jobs that match my preferences.
- Alert me on Telegram when a new matching job appears.
- Track my applications through a simple pipeline.
- Be honest about data: never claim to know a posting date that the source did not provide.

## 2. Non-goals (v1)

- No auto-apply. No login-bypassing. No LinkedIn or Naukri scraping.
- No multi-user accounts. Single user only.
- No AI features (resume matching, summaries). Possible v2.
- No public API. Possible v2 (FastAPI).
- No mobile app.

## 3. User

One user (me): a fresher in India looking for SDE, software development, QA, IT support, technical support, cloud, and networking roles.

## 4. Core rule: posted vs discovered

| Field | Meaning |
|---|---|
| `posted_at` | When the company posted it. Nullable. Only set if the source provides it. |
| `posted_at_source` | `api` / `parsed` / `none` |
| `first_seen_at` | When JobRadar first found it. Always set. |

UI wording:
- If `posted_at` exists: "Posted 2 Nov"
- If not: "Discovered today — posting date unavailable"

Store UTC. Display IST.

## 5. Features (v1)

1. Collect jobs from supported sources through adapters.
2. Monitor roles: SDE, software development, QA, IT support, technical support, cloud, networking, other tech.
3. Filter by level (fresher / experienced / unknown), location, company, category.
4. Show `posted_at` and `first_seen_at` honestly.
5. Telegram alerts for new matching jobs (batched digest if many).
6. Application tracker: Saved, Applied, Interview, Rejected, Offer, with notes.
7. Source health: show last run status per source; alert if a source fails or returns 0 / far fewer jobs.

## 6. Tech stack

| Part | Choice |
|---|---|
| Dashboard | Next.js + TypeScript + Tailwind CSS (Vercel) |
| Collectors | Python 3.11+ |
| Database | PostgreSQL on Neon (or Supabase) |
| Schema/migrations | SQLAlchemy + Alembic (Python owns schema) |
| DB access in web | `pg` with parameterized SQL, no ORM |
| Scheduling | GitHub Actions cron (every 30 min) |
| Notifications | Telegram Bot API |
| Backend API | None in v1 |

## 7. Data model

- `companies`: id, name
- `sources`: id, company_id, type (greenhouse/lever/ashby/custom), config (JSON), enabled, poll_interval_minutes
- `jobs`: id, source_id, external_id, fingerprint, title, company_id, locations (array), category, level, url, description (nullable), posted_at, posted_at_source, first_seen_at, last_seen_at, status (active/closed)
- `source_runs`: id, source_id, started_at, finished_at, status, jobs_found, new_count, error
- `preferences`: id, include_keywords, exclude_keywords, locations, levels, companies, categories
- `applications`: id, job_id, status (saved/applied/interview/rejected/offer), notes, created_at, updated_at
- `notifications`: id, job_id, sent_at, channel

Unique constraints: `jobs(source_id, external_id)`; index on `fingerprint`.

## 8. Reliability rules

- **Dedupe:** primary key `(source_id, external_id)`. Fallback `fingerprint` = hash of normalized company + title + location + requisition ID. Multi-location postings are one job with many locations.
- **Closed jobs:** if a job is missing for 3 consecutive successful runs of its source, mark `closed`. A failed run does not count toward closing.
- **Baseline run:** the first run of each source stores jobs with notifications off. Only jobs first seen after the baseline can trigger alerts.
- **No double alerts:** a job is notified at most once (`notifications` table).
- **Level detection:** parse "0-2 years" and keywords (graduate, trainee, associate, entry). Output `fresher / experienced / unknown`. Never guess silently.
- **Fixtures:** every adapter is tested against saved real responses so layout/API changes fail loudly.
- **Politeness:** clear User-Agent, timeouts, backoff, polling no faster than 30 minutes.

## 9. Sources

Phase A (prove the pipeline, public ATS APIs): a few Greenhouse, Lever, Ashby companies chosen by me.

Phase B (hard adapters, one per session, after A works): IBM, Accenture, TCS, Capgemini, Cognizant. For each, first investigate whether a JSON endpoint exists or a headless browser is needed. If too fragile, mark "manual / unsupported" instead of shipping something broken.

Campaign-based hiring (TCS NQT, Cognizant GenC, Accenture drives) is not covered by careers search; handle later with manual "Drive/Event" entries.

## 10. Build plan

| Step | Goal | Done when |
|---|---|---|
| 0 | Repo layout, docs, env setup | Folders exist, DB connects |
| 1 | Thin slice | Real jobs from one Greenhouse company appear on a web page |
| 2 | Trustworthy data | Dedupe, dates, last_seen/closed, source_runs, baseline run |
| 3 | Dashboard | Filters, preferences, "new today" and "matching" counts |
| 4 | Tracker | Application statuses and notes |
| 5 | Alerts and automation | Telegram, health alerts, GitHub Actions cron, Vercel deploy |
| 6 | More sources | More ATS companies, then hard adapters one by one |

## 11. Success criteria for MVP

- Runs automatically every 30 minutes without me touching it.
- A new matching job reaches Telegram within one polling interval of being discovered.
- No duplicate alerts and no flood on first run.
- A broken source is visible on the dashboard and in Telegram.
- I can track every application I make.

## 12. Open decisions

- Whether to add FastAPI in v1 (default: no).
- Final list of first Greenhouse/Lever/Ashby companies (to be chosen by me before Step 1).
