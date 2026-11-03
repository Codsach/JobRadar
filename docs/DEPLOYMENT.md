# JobRadar — Deployment Guide

This guide covers deploying the Next.js web dashboard to **Vercel**, hosting PostgreSQL on **Neon**, running scheduled collectors via **GitHub Actions**, and configuring **Telegram Bot** alerts.

---

## 1. Database Setup: Neon PostgreSQL

### Step 1.1 — Create a Neon Project
1. Log in to [Neon Console](https://console.neon.tech).
2. Create a new project named `jobradar`.
3. Neon provides two connection strings:
   - **Pooled connection string** (ends with `-pooler...`): Use for serverless runtimes like Vercel.
   - **Direct connection string**: Use for database migrations (Alembic) and scheduled jobs.

### Step 1.2 — Run Alembic Migrations
From your local environment or deployment terminal:
```bash
cd collectors
# Ensure DATABASE_URL is set in .env or exported in shell
alembic upgrade head
```
This provisions all tables: `companies`, `sources`, `jobs`, `source_runs`, `preferences`, `applications`, and `notifications`.

---

## 2. Web Dashboard Deployment: Vercel (`web/`)

### Step 2.1 — Import Project in Vercel
1. Log in to [Vercel](https://vercel.com) and click **Add New > Project**.
2. Select your `jobradar` Git repository.
3. In **Root Directory**, click **Edit** and set it to:
   ```
   web
   ```
4. Framework Preset: **Next.js** (detected automatically).
5. Build Command: `next build` (default).
6. Output Directory: `.next` (default).

### Step 2.2 — Environment Variables in Vercel
Add the following in Vercel's **Project Settings > Environment Variables**:

| Variable | Description | Example / Note |
|---|---|---|
| `DATABASE_URL` | Neon **pooled** connection string | `postgresql://user:pass@ep-xyz-pooler.region.neon.tech/jobradar?sslmode=require` |
| `AUTH_SECRET` | NextAuth secret key | Generate with `openssl rand -base64 32` |
| `AUTH_GITHUB_ID` | GitHub OAuth App Client ID | From GitHub Developer Settings |
| `AUTH_GITHUB_SECRET` | GitHub OAuth App Client Secret | From GitHub Developer Settings |
| `ALLOWED_GITHUB_USERNAME` | Single-user GitHub username | Your GitHub username |

Deploy the project. Your dashboard will be live at `https://<project-name>.vercel.app`.

---

## 3. Telegram Bot Setup

1. Open Telegram and message [@BotFather](https://t.me/botfather).
2. Run `/newbot`, name your bot (e.g., `MyJobRadarBot`), and save the generated **Bot Token**.
3. Create a private channel or group (or use direct chat with your bot), add your bot as an admin, and send a test message.
4. Obtain your **Chat ID** (e.g. using [@userinfobot](https://t.me/userinfobot) or `https://api.telegram.org/bot<TOKEN>/getUpdates`).
5. Add both to your `.env` and GitHub Secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

---

## 4. Automation: GitHub Actions (`collectors/`)

The workflow `.github/workflows/collectors.yml` automatically runs every 30 minutes.

### Step 4.1 — Add GitHub Actions Secrets
In your GitHub repository, navigate to **Settings > Secrets and variables > Actions** and create:

1. `DATABASE_URL`: Your Neon database connection string.
2. `TELEGRAM_BOT_TOKEN`: Your Telegram Bot API token.
3. `TELEGRAM_CHAT_ID`: Your Telegram chat ID.
4. `GREENHOUSE_BOARD_TOKEN`: (Optional, defaults to `stripe`).

### Step 4.2 — Manual Run / Verification
1. Navigate to the **Actions** tab in GitHub.
2. Select **Run JobRadar Collectors**.
3. Click **Run workflow** (`workflow_dispatch`) to trigger a collection run immediately.

---

## 5. Verification Checklist

- [ ] `alembic upgrade head` runs without errors and all migrations are applied.
- [ ] Vercel dashboard loads and displays active jobs and counters.
- [ ] First collector run on a source stores baseline jobs with notifications suppressed.
- [ ] Subsequent runs discover new jobs matching preferences and deliver real-time Telegram alerts.
- [ ] Second run with no new jobs sends zero duplicate alerts.
- [ ] Source health alerts trigger if an adapter fails or returns 0 jobs.

