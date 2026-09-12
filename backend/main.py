from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from app.routers import auth, users, resumes, skills, recommendations, interview, github, analytics
from app.services.llm import LLMError

import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Schema is owned by Alembic — run `alembic upgrade head` before starting.
# create_all() was removed because it silently no-ops on column changes to
# existing tables, which hid schema drift.


app = FastAPI(title="AI Career Coach API", version="1.0.0")

# Origins come from CORS_ORIGINS (comma-separated) so deployments don't need a
# code change. Defaults to the local Vite dev server.
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]

# Logged at startup because a CORS mismatch is invisible from the outside and
# its symptom is misleading: the browser blocks the response, and the UI reports
# "invalid credentials" or a bare 405 rather than a configuration problem. This
# line makes the deployed allow-list checkable in the host's logs.
logger.info("CORS allow-list: %s", CORS_ORIGINS)
if os.getenv("CORS_ORIGINS") is None:
    logger.warning(
        "CORS_ORIGINS is not set; falling back to %s. A deployed frontend on any "
        "other origin will have every request blocked by the browser.",
        DEFAULT_CORS_ORIGINS,
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(LLMError)
async def llm_error_handler(request: Request, exc: LLMError):
    """Surface AI failures as a retryable 503 carrying a user-safe message.

    Without this an unusable model response becomes an opaque 500, and the
    client can't tell "try again" from "something is broken".
    """
    logger.warning("LLM failure on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=503, content={"detail": str(exc)})


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(resumes.router)
app.include_router(skills.router)
app.include_router(recommendations.router)
app.include_router(interview.router)
app.include_router(github.router)
app.include_router(analytics.router)

@app.get("/")
def root():
    return {"message": "AI Career Coach API is running"}