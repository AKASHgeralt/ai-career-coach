# Project Context & Session Handoff

**Purpose of this file:** paste it (or point at it) at the start of a new Claude
session so the assistant has full context without re-reading the whole codebase.
It records what the project is, what was changed and why, what is verified,
what isn't, and the environment quirks that cost time to discover.

**Last updated:** 17 August 2026
**Repo:** `C:\Users\AKASHVEER\ai-career-coach`
**Branch:** `main` · **Last commit:** `76b4e0d` (pre-dates all work below)

> ⚠️ **All of the work described here is currently UNCOMMITTED** — roughly 80
> changed files, ~3,800 insertions sitting in the working tree. Committing is
> the first thing that should happen.

---

## 1. What this project is

**AI Career Coach ("CareerAI")** — a full-stack AI career intelligence platform.
A user picks a target job role, uploads a resume, and the system produces a
single **Career Readiness Score (0–100)** from four measured signals, then names
the single highest-value **next best action**.

The organising idea: it is *not* a collection of separate AI tools. Everything
feeds one score and one recommendation.

```
TARGET ROLE → RESUME → SKILL GAP → ROADMAP → INTERVIEW → GITHUB
                          ↓
              CAREER READINESS SCORE → NEXT BEST ACTION → (loop)
```

### Stack
- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic,
  Pydantic v2, JWT (python-jose) + bcrypt, PyMuPDF, Groq
  (`openai/gpt-oss-120b`, via `GROQ_MODEL`), httpx, pytest.
  No ML libraries: skill similarity is a committed lookup table.
- **Frontend:** React 19, Vite, React Router, axios, Tailwind, Framer Motion,
  Recharts, Lucide, oxlint
- **Infra:** Docker + compose + nginx (written, **never run** — see §7);
  free-tier deploy via Neon + Render + Vercel (`render.yaml`, `DEPLOYMENT.md`)

### Current size
- **227 tests** · **8 migrations** · **32 API endpoints**
- 17 backend services · 11 frontend components · 11 pages
- 0 lint warnings · frontend build clean

---

## 2. How to run and verify

```bash
# migrations FIRST — the app no longer creates tables on startup
cd backend && ./venv/Scripts/python.exe -m alembic upgrade head
cd backend && ./venv/Scripts/python.exe -m uvicorn main:app --reload --port 8000
cd frontend && npm run dev          # pinned to :5173, strictPort
```

```bash
# tests
cd backend
./venv/Scripts/python.exe -m pytest -m "not slow and not integration"  # ~13s, 159
./venv/Scripts/python.exe -m pytest                                     # ~100s, 213
```

Test credentials in the dev database: `akash@example.com` / `test1234`

---

## 3. Environment gotchas (these cost real time — read before debugging)

| Gotcha | Detail |
|---|---|
| **Browser pane freezes CSS transitions** | The preview pane doesn't composite frames, so `getComputedStyle` returns a transition's *start* value forever. An element can look stuck at its pre-animation position while being completely correct. **Set `element.style.transition='none'` before measuring.** This caused a long false-lead debugging the mobile drawer. |
| **`sheet.cssRules` throws** | Stylesheet introspection silently fails in the preview (cross-origin), so "no matching CSS rule found" is meaningless there. |
| **DB role can't `CREATE DATABASE`** | Test/baseline isolation uses a temporary **schema** with `search_path`, not a separate database. |
| **Port 5173 is load-bearing** | Backend CORS only allows `localhost:5173`. Vite is set `strictPort: true` so it fails loudly instead of drifting to 5174 — a drift once produced misleading "invalid credentials" errors. |
| **Windows paths** | Use `./venv/Scripts/python.exe`, not `python`. Bash tool available but PowerShell is primary. |
| **Patching LLM calls in tests** | Names are imported directly, so patch **where they are looked up**, not where they are defined: `app.routers.interview.generate_question`, not `interview_engine.generate_question`. Patching `llm.complete_text` does reach `complete_json`, which resolves it from `llm`'s globals at call time. Getting this wrong fires real Groq calls. |
| **Groq models get withdrawn** | `llama-3.3-70b-versatile` started returning 404 `model_not_found` mid-project. The model is now `GROQ_MODEL`, defaulting to `openai/gpt-oss-120b`. |
| **gpt-oss is a reasoning model** | It bills a private reasoning trace against the same `max_tokens` as the answer. Budgets sized for a non-reasoning model truncate mid-JSON. Keep `GROQ_REASONING_EFFORT=low`. |

---

## 4. What was done this session

Work followed a 24-phase upgrade brief. All phases were addressed.

| Area | Outcome |
|---|---|
| **Target role** | 7 roles in `services/roles.py`; drives skill baselines, roadmaps, interview questions, scoring. `users.target_role` + timestamp. |
| **Career readiness** | `services/readiness.py` — pure, deterministic, **no LLM**. Weights: skills 35 / resume 25 / interview 20 / github 20. Missing signals are excluded and weights renormalised — never counted as zero. Returns a written explanation. |
| **Next best action** | `services/next_action.py` — deterministic two-tier ladder (setup beats optimisation). Every reason is literally true of the user's data. |
| **Dashboard** | Rebuilt as a command centre: target role, readiness, 4 signal cards, next action, roadmap progress, timeline, top skill gaps. |
| **Resume versioning** | Per-user version numbers, comparison endpoint (skills gained/dropped/still-missing, per-category ATS deltas), improvement chart. |
| **ATS explainability** | Six-category breakdown with deficit-derived suggestions. Total unchanged. |
| **Skill classification** | MATCHED (≥0.75) / PARTIAL (≥0.50) / MISSING, with per-skill similarity persisted. |
| **Roadmap progress** | `roadmap_tasks` table; LLM asked for concrete weekly tasks; optimistic tick with rollback; progress on dashboard. |
| **Interview analytics** | 3 dimensions (technical, problem solving, communication) + strengths/weaknesses/practice. |
| **GitHub** | Typed errors, real rate-limit detection (403 + `X-RateLimit-Remaining: 0`), 60-min cache (7ms vs 890ms), evidence-only insights. |
| **Timeline** | Real recorded events only. No fabricated history. |
| **Migrations** | Alembic adopted onto the live DB via baseline + `stamp`. `create_all()` removed. |
| **Security** | 5MB cap, magic-byte validation, filename sanitisation, parse-before-write, env CORS, UUID-typed IDs, auth rate limiting. |
| **LLM reliability** | `services/llm.py` — Pydantic validation, one retry with the specific error fed back, then `LLMError` → 503. |
| **Performance** | Startup **23.4s → 1.2s**; install **1,331MB → 152MB**. spaCy, torch, faiss and sentence-transformers all removed; skill similarity is a committed lookup table with byte-identical output. |
| **Testing** | 0 → **227 tests**, including cross-user isolation across every router. |
| **Docs** | README written from verified facts (endpoints enumerated from OpenAPI, counts from pytest). |
| **Frontend** | Full dark "blueprint" redesign; responsive at 375/768/1440; nested routes. |
| **Docker** | All four placeholder files written. **Unverified.** |

---

## 5. Bugs found and fixed (worth knowing — several were silent)

1. **Interview answers graded against the wrong question.** `/start` generated a
   question, returned it, and threw it away; every answer in a session was then
   graded against one question the candidate never saw. Fixed by persisting
   `interview_sessions.current_question`. Your DB still shows the damage: one
   session has 4 answers against 1 distinct question.
2. **Every dashboard tab was unreachable.** `AnimatePresence mode="wait"` never
   completed its exit under React 19 StrictMode, so `main` never swapped. Also
   `Sidebar` was defined *inside* `Dashboard`, remounting on every render.
3. **Two competing ATS scorers.** Upload used a keyword count, analysis used the
   category breakdown — the same resume scored 60 and 83. This made the version
   improvement chart show phantom regressions. Unified.
4. **Non-UUID path params → 500 leaking SQL.** IDs were typed `str`, so `x`
   reached PostgreSQL. Now `UUID`-typed → 422.
5. **Silent LLM fallback.** An unparseable evaluation became a hardcoded score
   of 5, indistinguishable from a real grade. Now raises → 503.
6. **91px mobile overflow** — `main` had `flex-1` with default `min-width:auto`.
   Same trap hit again later in Settings (2px). Fix is `min-w-0`.
7. **Scrim remounted the sidebar** — conditionally rendering a sibling *before*
   `<Sidebar/>` shifted its tree position. Always render, toggle visibility.
8. **`.gitignore` swallowed `.env.docker.example`** — `.env.*` with only
   `!.env.example` excepted. Now `!.env.*.example`.
9. **Tests wrote 93 real files into `uploads/`** — truncating tables doesn't
   remove files. Since resolved at the source: nothing is written to disk at all
   any more. Uploaded PDFs are parsed in memory and discarded, and avatars are
   stored as bytes in the database, because free hosts wipe the filesystem on
   every restart.
10. **Roadmap generation failed 2 runs in 3** with "response was not valid JSON".
   It was truncation, not malformed output — the reasoning trace ate the token
   budget. `complete_text` now reports `finish_reason == "length"` honestly and
   `complete_json` doubles the budget on retry.

---

## 6. Design decisions — please don't silently undo these

- **Deterministic where it matters.** ATS score, skill classification, readiness
  and next-action are pure functions. The LLM only does open-ended generation
  (roadmaps, questions, grading prose). This is what makes scores explainable.
- **Missing data is never zero.** `score: null` with per-signal actions, not 0.
- **Nothing is invented.** GitHub insights deliberately say nothing about
  READMEs, tests or pinned repos because those are never fetched. Timeline has
  no historical readiness line because readiness was never snapshotted.
- **Only 3 interview dimensions.** The brief asked for 4 including *Confidence*.
  Confidence is a delivery trait and the interview is typed — scoring it would
  assert something never measured. Documented in code, README and UI.
- **LLM failure is loud.** Never substitute a plausible default.
- **`X-Forwarded-For` is ignored** by the rate limiter — any client can set it.
- **404 not 403** for other users' resources, so responses don't confirm
  existence.
- **Rate limiting scope is stated honestly** — in-process, so with N workers the
  real limit is ~limit×N. It's a speed bump, not edge enforcement.

---

## 7. What is NOT verified

- **Docker.** `docker compose up --build` has never been run — Docker isn't
  installed on this machine. Compose YAML parses; Dockerfiles are unproven.
- **Frontend tests.** None exist; no test runner configured in `package.json`.
- **Real interview end-to-end.** Only ~1–2 real Groq-backed answers were run;
  a full 5-question session with real answers hasn't been done.
- **Production deploy** of any kind.

---

## 8. Outstanding work

**Blocked on the user:**
- `LICENSE` — none exists. MIT is the usual choice for a portfolio project.
- **Screenshots** — README section written and waiting; `docs/screenshots/`.
- **Run `docker compose up --build`** once Docker is installed.

**Optional / nice to have:**
- Refresh tokens (access tokens expire in 30 min, no refresh flow)
- Roadmap adaptation (Phase 9 of the brief) — reprioritising based on interview
  weaknesses and completed tasks was designed for but only partly realised
- Deeper GitHub analysis (README/tests) — needs authenticated API calls
- 5 stale `active` interview sessions in the dev DB from before fix #1. They
  return a clear 409; harmless but can be deleted.
- `smoketest_verify@example.com` is a leftover user in the dev DB.

---

## 9. File map (the parts that matter)

```
backend/app/services/
  roles.py               target role catalogue — add a role here, one line
  readiness.py           pure scoring maths (weights, renormalisation)
  readiness_data.py      gathers the 4 signals from the DB
  next_action.py         deterministic recommendation ladder
  nlp.py                 skill extraction + ATS breakdown (regex, no spaCy)
  skill_gap_engine.py    embeddings + FAISS, lazy-loaded, 0.75/0.50 thresholds
  llm.py                 validated LLM calls, retry, LLMError
  roadmap_tasks.py       task materialisation + progress
  interview_analytics.py dimension aggregation
  github_analyzer.py     API client, rate-limit detection
  github_insights.py     evidence-only strengths/weaknesses
  timeline.py            real recorded events
  resume_versions.py     version history + comparison
  rate_limit.py          in-process auth throttling

frontend/src/
  pages/Dashboard.jsx        layout shell (sidebar + <Outlet/>)
  pages/Overview.jsx         the dashboard overview, its own route
  pages/dashboardSections.js label → path map (single source of truth)
  components/                one per feature panel
```

**Database (8 tables):** users, resumes, skill_gaps, recommendations,
roadmap_tasks, interview_sessions, interview_answers, github_profiles.

---

## 10. Suggested first message for a new session

> I'm working on the AI Career Coach project at
> `C:\Users\AKASHVEER\ai-career-coach`. Read `PROJECT_CONTEXT.md` in the repo
> root first — it has the full history, design decisions and known issues.
> [then your request]
