# AGENTS.md — JobRadar

Read this file and `docs/PRD.md` at the start of every session.

## Project layout

```
jobradar/
├── AGENTS.md
├── docs/
│   ├── PRD.md
│   └── PROMPTS.md
├── web/          # Next.js + TypeScript + Tailwind (dashboard, READ-ONLY on job data)
└── collectors/   # Python (collectors, migrations, Telegram, scheduled runs)
```

## Ownership rules

- **Python owns the database schema.** Schema changes happen only through Alembic migrations in `collectors/`.
- `web/` reads the database with parameterized SQL (`pg`). No ORM in `web/`. The only tables `web/` may write to are `applications`, `preferences`, `companies`, and `sources`.
  - `companies` and `sources` writes happen only via the "Add Company" server action (`web/src/app/actions/companies.ts`), which requires an active session, uses ON CONFLICT DO NOTHING, and never fabricates data.
- Never edit the schema from `web/`.

## Working rules

1. **One step at a time.** Do only the step named in the prompt. Do not start later steps or add unrequested features.
2. **Plan first.** Before writing code, output an implementation plan (files to create/change, commands to run, how you will verify). Wait for approval.
3. **Never fabricate data.** No fake jobs, invented API endpoints, or made-up company IDs. If a real endpoint or response is unknown, say so and ask, or fetch it and save the real response as a fixture.
4. **Never guess dates.** `posted_at` is nullable. If the source gives no reliable posting date, leave it null and set `posted_at_source = 'none'`. `first_seen_at` is always set by the system.
5. **Reuse before rebuilding.** Modify existing code and components instead of rewriting them.
6. **Ask before adding dependencies.** List the package and why.
7. **Verify before saying done.** Run the code, run the tests, and report the actual output. If something could not be run, say so.
8. **Small commits.** Finish a step with a summary of changed files and a suggested commit message.

## Collector rules

- One adapter per source in `collectors/adapters/`. Adding a source = one new file + one config row. No changes to core code.
- Every adapter implements the `Collector` interface: `fetch()` returns raw jobs, `normalize()` returns `Job`.
- Each adapter has a test that runs against a **saved real response** in `collectors/tests/fixtures/`.
- Prefer official/public JSON APIs (Greenhouse, Lever, Ashby, SmartRecruiters, Workable). Check `robots.txt` and terms first.
- Use a clear `User-Agent`, a timeout, and retries with backoff. Poll no more often than every 30 minutes.
- Do not scrape LinkedIn or Naukri. Do not bypass logins, CAPTCHAs, or bot protection. Do not auto-apply to jobs.
- Every run writes a `source_runs` row, including failures.

## Code style

- Python 3.11+, type hints, `ruff` for lint/format, `pytest` for tests.
- TypeScript strict mode, App Router, server components for data reading.
- Times stored in UTC; displayed in IST (Asia/Kolkata).
- Secrets only in environment variables. Never commit `.env`. Keep `.env.example` updated.

## Output format

- Keep explanations short. Lead with the plan, then the result.
- When the task is implementation, the deliverable is the code and files, plus a brief verification report.
