"""
Root conftest – loads .env before any test runs.

Rules (per AGENTS.md):
- Load .env only if the file exists (silently skip otherwise).
- Never override variables that are already set in the environment.
  In GitHub Actions the real env vars are used; .env is never present.
"""
from pathlib import Path

from dotenv import load_dotenv

# Walk up from collectors/ to the repo root so this works regardless of
# where pytest is invoked from.
_repo_root = Path(__file__).resolve().parent.parent
_env_file = _repo_root / ".env"

load_dotenv(dotenv_path=_env_file, override=False)

