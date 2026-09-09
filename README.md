# AI Career Coach

An AI career intelligence platform that continuously measures how ready you are
for a target job role, and tells you exactly what to improve next.

Rather than a collection of separate AI tools, every feature feeds one number —
the **Career Readiness Score** — and one recommendation: your **next best action**.

---

## Contents

- [Overview](#overview)
- [The problem](#the-problem)
- [The solution](#the-solution)
- [Key features](#key-features)
- [The AI/ML pipeline](#the-aiml-pipeline)
- [System architecture](#system-architecture)
- [Tech stack](#tech-stack)
- [Database architecture](#database-architecture)
- [API overview](#api-overview)
- [Project structure](#project-structure)
- [Installation](#installation)
- [Environment variables](#environment-variables)
- [Deployment](#deployment)
- [Running locally](#running-locally)
- [Example workflow](#example-workflow)
- [Testing](#testing)
- [Design decisions](#design-decisions)
- [Screenshots](#screenshots)
- [Future improvements](#future-improvements)

---

## Overview

Upload a resume, pick a target role, and the platform scores your readiness out
of 100 from four measured signals — resume quality, skill match, interview
performance and GitHub activity. It then names the single highest-value thing
you should do next, and explains why in terms of your own data.

Everything is connected:

```
TARGET ROLE
    ↓
RESUME ANALYSIS ──────┐
    ↓                 │
SKILL GAP ────────────┤
    ↓                 ├──→ CAREER READINESS SCORE ──→ NEXT BEST ACTION
LEARNING ROADMAP ─────┤                                      │
    ↓                 │                                      │
MOCK INTERVIEW ───────┤                                      │
    ↓                 │                                      ↓
GITHUB ANALYSIS ──────┘                              (repeat the loop)
```

---

## The problem

Job seekers get plenty of isolated feedback — an ATS checker here, a mock
interview tool there — but nothing tells them **where they actually stand** for a
specific role, or **what to do first**. The result is busywork: polishing a
resume that's already fine while a missing core skill goes unaddressed.

Generic AI tools make this worse by producing confident, unverifiable output.
A number with no explanation is not actionable.

---

## The solution

Three principles shape the whole system:

**1. One score, fully explainable.**
The readiness score is a deterministic weighted average of four measured
signals. No LLM decides it. Every point traces to a component you can inspect,
and the API returns a plain-language explanation of what drove the result.

**2. Missing data is never punished.**
Haven't connected GitHub? It is excluded and the remaining weights are
renormalised — you are not scored 0 for something you simply haven't done yet.
The API says exactly which signals are missing and what to do about each.

**3. Nothing is invented.**
Every displayed claim is derived from data actually collected. The GitHub
insights don't mention READMEs or test coverage, because the app never fetches
them. When an LLM returns something unusable, the request fails with a clear
error rather than substituting a plausible-looking default.

---

## Key features

| Feature | What it does |
|---|---|
| **Target role** | Seven supported roles drive skill baselines, roadmaps, interview questions and scoring. Adding a role is a one-line change. |
| **Resume analysis** | PDF text extraction, skill detection, and a deterministic ATS score broken down into six explainable categories with specific improvement suggestions. |
| **Resume versioning** | Each upload is a numbered version. Compare any two to see skills gained, skills dropped, what your target role still requires, and how each ATS category moved. |
| **Skill gap engine** | Exact matching plus a precomputed similarity table. Classifies each required skill as MATCHED / PARTIAL / MISSING with a similarity score. |
| **Career readiness score** | 0–100, weighted across four signals, with graceful handling of missing data and a written explanation. |
| **Next best action** | Deterministic engine that names the single highest-value next step and justifies it with your own numbers. |
| **Learning roadmap** | LLM-generated week-by-week plan with courses, projects and books — materialised into checkable tasks with persisted progress. |
| **Mock interviews** | AI-generated questions that never repeat, scored answers with structured feedback. |
| **GitHub analyzer** | Developer score plus evidence-based strengths, weaknesses and recommended actions. Cached to respect API rate limits. |

---

## The AI/ML pipeline

```
                        ┌──────────────────┐
   Resume PDF ─────────→│  PyMuPDF extract │  (parsed in memory, never
                        └────────┬─────────┘   written to disk until valid)
                                 ↓
                        ┌──────────────────┐
                        │ Skill extraction │  regex + alias map over a
                        └────────┬─────────┘  ~90-skill vocabulary
                                 ↓
                    ┌────────────┴────────────┐
                    ↓                         ↓
         ┌────────────────────┐   ┌───────────────────────┐
         │  ATS scoring       │   │  Target role baseline │
         │  (deterministic,   │   │  17 role profiles     │
         │   6 categories)    │   └───────────┬───────────┘
         └─────────┬──────────┘               ↓
                   │              ┌────────────────────────┐
                   │              │  Similarity lookup     │
                   │              │  precomputed table     │
                   │              │  score ≥ 0.75 MATCHED  │
                   │              │        ≥ 0.50 PARTIAL  │
                   │              └────────────┬───────────┘
                   │                           ↓
                   │                   ┌──────────────┐
                   │                   │  Skill gap   │
                   │                   └──────┬───────┘
                   │                          ↓
                   │              ┌───────────────────────┐
                   │              │  Roadmap generation   │
                   │              │  Groq / gpt-oss-120b  │
                   │              │  Pydantic-validated   │
                   │              └───────────┬───────────┘
                   │                          ↓
                   │                  ┌───────────────┐
                   │                  │ Mock interview│
                   │                  └───────┬───────┘
                   ↓                          ↓
         ┌─────────────────────────────────────────────┐
         │        CAREER READINESS SCORE               │
         │  resume 25% · skills 35% · interview 20%    │
         │  · github 20% (renormalised when missing)   │
         └──────────────────┬──────────────────────────┘
                            ↓
                  ┌────────────────────┐
                  │  Next best action  │  deterministic, no LLM
                  └────────────────────┘
```

### Why this split

**Deterministic where it matters.** The ATS score, skill classification,
readiness score and next-best-action are all pure functions. They are
reproducible, unit-testable, and explainable to the user. An LLM is used only
where open-ended generation is genuinely required: writing roadmaps, asking
interview questions and grading free-text answers.

**Two-stage skill matching.** Exact set intersection first — unambiguous and
free. Only unresolved skills fall through to the similarity table. Thresholds
turn a binary match into three actionable categories.

The table was generated offline from `all-MiniLM-L6-v2`. `SKILLS_DB` is a closed
vocabulary, so every pair the model could ever be asked about was enumerated once
and the answers baked in — 26 pairs scored above zero out of 3,081. That produces
identical output while removing torch, faiss and sentence-transformers from the
install, which took it from 1,331 MB to 152 MB and made free hosting viable. See
`backend/app/services/skill_similarity.py`.

**Structured LLM output.** Every LLM call that must return data is validated
against a Pydantic model, retried once with the specific validation error fed
back, and raised as an error if it still fails. A malformed response never
becomes silent application data.

---

## System architecture

```
┌───────────────────────────┐         ┌────────────────────────────────┐
│  React SPA (Vite :5173)   │         │   FastAPI (uvicorn :8000)      │
│                           │         │                                │
│  pages/      components/  │  HTTPS  │  routers/  →  services/        │
│  api/  ──── axios ────────┼────────→│     ↓            ↓             │
│  JWT in localStorage      │  Bearer │  schemas/     SQLAlchemy ORM   │
└───────────────────────────┘         └───────┬────────────┬───────────┘
                                              │            │
                              ┌───────────────┘            └────────────┐
                              ↓                                         ↓
                    ┌───────────────────┐                  ┌────────────────────┐
                    │   PostgreSQL      │                  │  External services │
                    │   8 tables        │                  │  • Groq (LLM)      │
                    │   Alembic-managed │                  │  • GitHub REST API │
                    └───────────────────┘                  └────────────────────┘
```

Request flow: `router` (auth, HTTP concerns) → `service` (business logic, pure
where possible) → `model` (persistence). Pydantic schemas validate every
boundary in both directions.

---

## Tech stack

**Backend** — Python 3.11
| Purpose | Choice |
|---|---|
| Web framework | FastAPI, uvicorn |
| ORM / database | SQLAlchemy 2.0, PostgreSQL, psycopg2 |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | passlib + bcrypt, python-jose (JWT HS256) |
| PDF parsing | PyMuPDF |
| Skill similarity | precomputed lookup table (generated offline) |
| LLM | Groq — `openai/gpt-oss-120b` (set `GROQ_MODEL`) |
| HTTP client | httpx |
| Testing | pytest |

**Frontend** — React 19
| Purpose | Choice |
|---|---|
| Build | Vite |
| Routing | React Router |
| HTTP | axios |
| Styling | Tailwind CSS |
| Animation | Framer Motion |
| Charts | Recharts |
| Icons | Lucide |
| Linting | oxlint |

---

## Database architecture

Eight tables, all UUID primary keys, managed entirely by Alembic.

```
users ─────┬──── resumes ──────── skill_gaps ──────── recommendations ──── roadmap_tasks
           │      (ATS score,      (matched /          (courses, projects,   (week, title,
           │       parsed text)     partial /           books, roadmap)       completed)
           │                        missing +
           │                        similarity)
           │
           ├──── interview_sessions ──── interview_answers
           │      (current_question,      (question, answer,
           │       total_score)            score, feedback)
           │
           └──── github_profiles
                  (developer_score, repos, languages, synced_at)
```

| Table | Notable columns |
|---|---|
| `users` | `target_role`, `target_role_updated_at` |
| `resumes` | `parsed_text`, `ats_score`, `version` (per-user sequential) |
| `skill_gaps` | `matched_skills`, `missing_skills`, `skill_details` (per-skill status + similarity), `match_score`, `used_role_fallback` |
| `recommendations` | `courses`, `projects`, `books`, `roadmap` (JSON) |
| `roadmap_tasks` | `week`, `title`, `position`, `completed`, `completed_at` |
| `interview_sessions` | `current_question` — the pending question, so answers are graded against what the candidate actually saw |
| `interview_answers` | `question`, `answer`, `score`, `ai_feedback`, `dimensions` (per-dimension 0-10), `strengths`, `improvements` |
| `github_profiles` | `developer_score`, `repos`, `top_languages`, `synced_at` |

Migrations:

```
80d0152fdbab  baseline existing schema
0add6bdb5c03  add user target role
8a5d68c66fe4  add roadmap tasks
319ebdeb8386  add skill gap details
2e65cf1da8e1  add interview answer dimensions
ca6116dbeba4  add resume version (backfilled by upload order)
```

---

## API overview

31 endpoints. Everything except `/` and `/api/auth/*` requires
`Authorization: Bearer <jwt>`.

**Auth**
```
POST   /api/auth/register            JSON {full_name, email, password}
POST   /api/auth/login               form-encoded (username=email, password)
```

**Users**
```
GET    /api/users/me
GET    /api/users/target-roles       catalogue of selectable roles
PUT    /api/users/me/target-role     {target_role: "ai-engineer"}
POST   /api/users/me/avatar          multipart
DELETE /api/users/me/avatar
```

**Resumes**
```
POST   /api/resumes/upload           multipart, PDF only, 5MB cap
GET    /api/resumes
GET    /api/resumes/{id}
GET    /api/resumes/{id}/analyze     NLP analysis + ATS breakdown
GET    /api/resumes/versions         version history + ATS series
GET    /api/resumes/compare          ?base=&target= — skill and category deltas
DELETE /api/resumes/{id}             cascades to gaps, recommendations, tasks
```

**Skills**
```
POST   /api/skills/analyze           {resume_id, job_title?, job_description}
GET    /api/skills/gaps/{resume_id}
```

**Recommendations & roadmap**
```
POST   /api/recommendations/roadmap        {gap_id, target_role}
GET    /api/recommendations/{gap_id}
GET    /api/recommendations/{gap_id}/tasks tasks + progress
PATCH  /api/recommendations/tasks/{id}     {completed: true}
```

**Interview**
```
POST   /api/interview/start          {job_role?, difficulty}
POST   /api/interview/answer         {session_id, answer}
GET    /api/interview/sessions
GET    /api/interview/sessions/{id}/answers
GET    /api/interview/sessions/{id}/analytics   dimension breakdown
```

**GitHub**
```
POST   /api/github/connect           {github_username, force?}
GET    /api/github/profile
```

**Analytics**
```
GET    /api/analytics/summary
GET    /api/analytics/readiness      score, components, next action, skill gaps
GET    /api/analytics/timeline       real recorded events + per-signal series
```

Interactive docs at `http://localhost:8000/docs`.

### Error semantics

| Status | Meaning |
|---|---|
| `400` | Invalid input — bad PDF, empty file, unknown role |
| `401` | Missing or expired token |
| `409` | Interview session has no pending question |
| `413` | Resume exceeds the 5MB limit |
| `429` | Too many login/sign-up attempts, or GitHub rate limit reached — both carry `Retry-After` |
| `502` | GitHub unreachable |
| `503` | LLM returned an unusable response after a retry |

---

## Project structure

```
ai-career-coach/
├── backend/
│   ├── main.py                     app, CORS, lifespan, error handlers
│   ├── database.py                 engine, session, Base
│   ├── alembic/versions/           4 migrations
│   ├── tests/                      213 tests
│   └── app/
│       ├── models/                 SQLAlchemy ORM (8 tables)
│       ├── schemas/                Pydantic request/response models
│       ├── routers/                auth, users, resumes, skills,
│       │                           recommendations, interview, github, analytics
│       └── services/
│           ├── auth.py             hashing, JWT
│           ├── nlp.py              skill extraction, ATS breakdown
│           ├── skill_gap_engine.py matching, similarity, classification
│           ├── readiness.py        pure scoring maths
│           ├── readiness_data.py   gathers signals from the DB
│           ├── next_action.py      deterministic recommendation engine
│           ├── interview_analytics.py  dimension aggregation
│           ├── timeline.py         real career events
│           ├── resume_versions.py  version history and comparison
│           ├── roadmap_tasks.py    task materialisation and progress
│           ├── llm.py              validated LLM calls with retry
│           ├── recommendation_engine.py
│           ├── interview_engine.py
│           ├── github_analyzer.py  API client, rate-limit handling
│           ├── github_insights.py  evidence-based strengths/weaknesses
│           └── roles.py            target role catalogue
└── frontend/
    └── src/
        ├── api/                    one module per backend router
        ├── components/             CareerReadiness, NextBestAction,
        │                           RoadmapProgress, SkillClassification,
        │                           AtsBreakdown, GithubInsights,
        │                           TargetRoleSelector, Wire
        └── pages/                  Landing, Login, Register,
                                    Dashboard (layout), Overview,
                                    Resumes, Skillgap, Roadmap, Interview,
                                    Github, Settings
```

---

## Installation

**Prerequisites:** Python 3.11+, Node 18+, PostgreSQL 14+, and a
[Groq API key](https://console.groq.com) (free tier is sufficient).

```bash
git clone <your-repo-url>
cd ai-career-coach
```

**Database**

```bash
createdb career_coach
```

**Backend**

```bash
cd backend
python -m venv venv
venv/Scripts/activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

**Frontend**

```bash
cd frontend
npm install
```

---

## Environment variables

Create `backend/.env` (see `.env.example`):

```ini
# Required
DATABASE_URL=postgresql://user:password@localhost:5432/career_coach
SECRET_KEY=<a long random string>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GROQ_API_KEY=<your groq key>

# Optional
CORS_ORIGINS=http://localhost:5173      # comma-separated
GITHUB_TOKEN=<pat>                      # raises GitHub limit 60/hr → 5000/hr
GITHUB_CACHE_MINUTES=60                 # reuse window for GitHub data
GROQ_MODEL=openai/gpt-oss-120b          # override if Groq withdraws the model
GROQ_REASONING_EFFORT=low               # low | medium | high | none
```

`.env` is gitignored. Never commit real credentials.

---

## Deployment

The whole stack runs on free tiers with no card required — Neon for Postgres,
Render for the API, Vercel or Cloudflare Pages for the frontend. `render.yaml`
and `frontend/vercel.json` are committed, so most of it is a blueprint import.

**[Full instructions: DEPLOYMENT.md](DEPLOYMENT.md)**

This is only possible because the backend install is ~150 MB and writes nothing
to disk; the earlier torch-based build needed 1.3 GB and a persistent volume,
which no free tier offers.

---

## Running with Docker

```bash
cp .env.docker.example .env     # then fill in SECRET_KEY, GROQ_API_KEY, POSTGRES_PASSWORD
docker compose up --build
```

Then open http://localhost:8080.

Three services: Postgres, the FastAPI backend, and nginx serving the built
frontend. The backend waits for a healthy database, applies migrations on
start, and reports healthy once it can serve — so the frontend only comes up
once the API is actually answering.

nginx proxies `/api` to the backend from the same origin, so no browser request
is cross-origin and CORS doesn't apply to this deployment. The frontend image is
built with `VITE_API_URL=""` for that reason.

Database files live on a named volume and survive `docker compose down`; use
`down -v` to discard them. There is no uploads volume — nothing is written to
disk at runtime.

> Not yet run end to end — Docker wasn't available on the machine this was
> written on. The compose file parses and the frontend build was verified in
> both configurations, but treat the first `up --build` as unproven.

---

## Running locally

**1. Apply migrations** (required — the app no longer creates tables on startup):

```bash
cd backend && venv/Scripts/python.exe -m alembic upgrade head
```

**2. Start the backend:**

```bash
cd backend && venv/Scripts/python.exe -m uvicorn main:app --reload --port 8000
```

**3. Start the frontend:**

```bash
cd frontend && npm run dev
```

Open http://localhost:5173.

> The dev server is pinned to port 5173 (`strictPort`). If that port is taken it
> fails loudly rather than silently moving to 5174, which the backend's CORS
> policy would reject — producing confusing "invalid credentials" errors.

---

## Example workflow

1. **Register** and sign in.
2. **Choose a target role** in Settings — say *Machine Learning Engineer*. The
   dashboard prompts for this, because nothing can be personalised without it.
3. **Upload a resume.** You get an ATS score with a six-category breakdown and
   specific suggestions.
4. **Run a skill gap analysis.** Paste a job description, or leave it blank to
   compare against your target role's baseline. Each required skill comes back
   MATCHED, PARTIAL or MISSING with a similarity score.
5. **Check your readiness score.** Say 46.3/100, with the explanation
   *"Resume / ATS is your strongest at 83, and Interview is holding you back
   most at 22."*
6. **Follow the next best action.** Perhaps *"Close your biggest skill gap:
   Docker — it's missing from 3 of your 4 analyses and carries the most weight."*
7. **Generate a roadmap** and tick off weekly tasks. Progress persists and
   appears on the dashboard.
8. **Practise interviews** and **connect GitHub** to light up the remaining
   signals.
9. **Watch the score move** and get a new recommendation. Repeat.

---

## Testing

```bash
cd backend
venv/Scripts/python.exe -m pytest -m "not integration"                # unit only, ~12s
venv/Scripts/python.exe -m pytest -m integration                      # API tests, needs a database
venv/Scripts/python.exe -m pytest                                     # everything, ~95s
```

Integration tests build a throwaway PostgreSQL **schema** by running the real
Alembic migrations, then drop it. Development data is never touched, and a
broken migration fails the suite rather than surfacing later.

**227 tests**, concentrated on logic that must not silently drift:

| Suite | Covers |
|---|---|
| `test_readiness.py` (15) | Weighted scoring, renormalisation, missing-data handling, explanations |
| `test_github.py` (19) | Evidence-based insights, rate-limit detection, developer score |
| `test_llm_reliability.py` (23) | JSON extraction, schema validation, retry, truncation, explicit failure |
| `test_api_avatars.py` (11) | Image sniffing, database round-trip, cache busting, removal |
| `test_upload_security.py` (15) | Size limits, magic bytes, filename sanitisation |
| `test_roadmap_tasks.py` (15) | Task materialisation, malformed LLM input, progress |
| `test_ats_breakdown.py` (15) | Category scoring, suggestions, total preservation |
| `test_next_action.py` (12) | Decision ladder, weakest-signal targeting |
| `test_lazy_loading.py` (5) | Startup performance regression guards |
| `test_interview_analytics.py` (14) | Dimension aggregation, legacy sessions, practice suggestions |
| `test_timeline.py` (7) | Event series, single-point-is-not-a-trend |
| `test_resume_versions.py` (18) | Version numbering, skill deltas, ATS comparison |
| `test_api_auth.py` (33) | Registration, login, token forgery/expiry, route protection |
| `test_api_isolation.py` (18) | Cross-user data isolation across every router |
| `test_rate_limit.py` (9) | Window expiry, per-client keys, brute-force throttling |

The suite deliberately targets **behavioural invariants**, not line coverage.
Examples: a missing signal must never be reported as your weakest area; an
unparseable LLM response must raise rather than become a score of 5; skill
matching must work with torch and faiss absent from the environment entirely.

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

---

## Design decisions

**Alembic adopted onto a live database.** The project originally used
`create_all()`, which creates missing tables but silently ignores column changes
— so the schema drifted from the models. The baseline migration was generated
against a scratch schema, then `alembic stamp` marked the existing database as
current without re-running DDL or touching data.

**The embedding model became a lookup table.** Semantic matching accounted for
8.1% of matches, and across all 3,081 pairs in the closed `SKILLS_DB` vocabulary
the model scored exactly 26 above zero. Those were computed once offline and
committed as a table, so torch, faiss, transformers and sentence-transformers
left the install: 1,331 MB → 152 MB, import 23.4s → 1.2s, output byte-identical.
`test_dependency_footprint.py` fails if any of them returns.

**Reasoning models bill their thinking to the answer's budget.** gpt-oss emits a
private reasoning trace before its reply, drawn from the same `max_tokens`. The
budgets had been sized for a non-reasoning model, so roadmap generation was
truncated mid-JSON two runs in three — and reported as *"not valid JSON"*, which
points at the wrong thing. `complete_text` now detects `finish_reason == "length"`
and says the limit was hit; `complete_json` doubles the budget on retry instead
of repeating a request that cannot fit. `GROQ_REASONING_EFFORT=low` cuts the
trace to ~10-40 tokens and roadmap latency from ~18s to ~3s, with identical
grades (a strong answer scores 8, a weak one 2, at either setting).

**Nothing is written to disk at runtime.** Uploaded PDFs are parsed in memory and
never stored — no endpoint ever served them back, and only the extracted text is
used. Avatars are held as bytes in the database. Both changes exist because the
free hosting tiers restart containers on idle, which silently emptied the upload
directory while the rows kept pointing into it.

**GitHub caching.** Unauthenticated GitHub allows 60 requests/hour and each sync
costs two. Profiles are reused within a configurable window — a cached read is
~7ms versus ~890ms live — and the Refresh button forces a re-fetch.

**Dashboard sections are real routes.** `/dashboard/resumes`,
`/dashboard/interview` and so on are nested routes under a layout, not tab
state. Refresh keeps your place, the back button works, and sections can be
bookmarked and shared. `dashboardSections.js` maps section label to path in one
place, so the sidebar and every call-to-action stay in sync.

**Rate limiting is honest about its scope.** Login and registration are
throttled per client address, which stops an unthrottled password oracle. The
counters live in process memory, so with multiple workers the effective limit
is roughly `limit x workers` and everything resets on restart — a real speed
bump against credential stuffing, not edge enforcement. `X-Forwarded-For` is
deliberately ignored, since any client can set it and rotate their own key.

**Tests own their environment.** Integration tests run against a migrated
throwaway schema rather than the development database. The alternative — testing against real data — makes failures
depend on whatever happens to be in the database that day.

**One ATS scorer everywhere.** The upload path originally used a separate
keyword-count scorer while analysis used the category breakdown, so the same
resume scored 60 on upload and 83 after analysis — which made the version
improvement chart show phantom regressions. Both now use the same function.

**UUID-typed identifiers.** Path and query parameters carrying IDs are typed
`UUID`, so a malformed value returns 422 at validation instead of reaching
PostgreSQL and surfacing a driver error in a 500.

**Three interview dimensions, not four.** Technical knowledge, problem solving
and communication are graded because a written answer evidences them.
"Confidence" is deliberately excluded: it is a delivery trait — tone, hesitation,
pacing — and this interview is typed, so scoring it would mean asserting
something never measured. It becomes available if voice interviews are added.

**Similarity thresholds.** 0.75 for MATCHED is strict enough to avoid claiming
merely-related technologies as held skills; 0.50 marks adjacent knowledge as
PARTIAL, because "you're close" is different advice from "start here".

---

## Screenshots

> Not yet captured. To add them, run the app, take screenshots of the
> dashboard, skill gap and roadmap views, save them under `docs/screenshots/`,
> and embed them here:
>
> ```markdown
> ![Dashboard](docs/screenshots/dashboard.png)
> ```

---

## Future improvements

- **Adaptive roadmaps** — reprioritise based on interview weaknesses and
  completed tasks
- **Deeper GitHub analysis** — commit cadence, README and test detection
  (requires authenticated API calls)
- **Refresh tokens** — access tokens expire in 30 minutes with no refresh flow

---

## License

MIT — see [LICENSE](LICENSE).
