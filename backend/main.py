from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from fastapi import Request
from fastapi.responses import JSONResponse

from app.routers import auth, users, resumes, skills, recommendations, interview, github, analytics
from app.services.llm import LLMError

import logging
import os
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Schema is owned by Alembic — run `alembic upgrade head` before starting.
# create_all() was removed because it silently no-ops on column changes to
# existing tables, which hid schema drift.


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm the embedding model without delaying startup.

    The model takes ~30s to load. Loading it lazily meant the first skill-gap
    request paid that cost, which reads as a hung request. Loading it
    synchronously here would instead make the server unavailable for 30s.

    Default is a background thread: the API serves immediately and the model
    loads alongside, so by the time a user logs in and navigates to skill gap
    it is normally ready. get_model() is guarded by a double-checked lock, so a
    request arriving mid-load simply waits for the same instance.

      WARM_UP_MODELS=background  (default) load concurrently with startup
      WARM_UP_MODELS=1|blocking            finish loading before serving
      WARM_UP_MODELS=0|off                 don't warm; first request pays
    """
    mode = os.getenv("WARM_UP_MODELS", "background").strip().lower()

    if mode in ("0", "false", "no", "off"):
        logger.info("Model warm-up disabled; first skill-gap request will load it")
    elif mode in ("1", "true", "yes", "blocking"):
        from app.services.skill_gap_engine import warm_up
        logger.info("Loading embedding model before serving…")
        warm_up()
    else:
        from app.services.skill_gap_engine import warm_up

        def _warm():
            try:
                warm_up()
                logger.info("Embedding model ready")
            except Exception:
                # A failed warm-up must not take the server down; the next
                # request retries the load and surfaces any real error.
                logger.warning("Background model warm-up failed", exc_info=True)

        threading.Thread(target=_warm, name="model-warmup", daemon=True).start()

    yield


app = FastAPI(title="AI Career Coach API", version="1.0.0", lifespan=lifespan)

# Origins come from CORS_ORIGINS (comma-separated) so deployments don't need a
# code change. Defaults to the local Vite dev server.
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads/avatars", exist_ok=True)
app.mount("/uploads/avatars", StaticFiles(directory="uploads/avatars"), name="avatars")

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