from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator
import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from .config import load_settings
from .db import db, Database
from .routers import topics as topics_router
from .routers import questions as questions_router
from .routers import streak as streak_router
from .routers import generate as generate_router


settings = load_settings()

# Configure basic logging if not already configured (e.g. when not running via uvicorn's logger)
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
timing_logger = logging.getLogger("app.timing")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # For serverless (Vercel), skip explicit connect since we use lazy connection
    # Only initialize schema if needed (typically for local dev with empty DB)
    is_serverless = os.getenv("VERCEL", "") != ""
    
    if not is_serverless:
        await db.connect()
        schema_path = Path(__file__).parent / "sql" / "schema.sql"
        await db.init_schema(schema_path)
    
    yield
    
    if not is_serverless:
        await db.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Temporarily allow all origins for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trust proxy headers for correct scheme/host detection behind reverse proxy
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")


@app.middleware("http")
async def record_request_timing(request: Request, call_next):
    start_time = time.perf_counter()
    method = request.method
    path = request.url.path

    try:
        response = await call_next(request)
        status_code = getattr(response, "status_code", 0)
        duration_seconds = time.perf_counter() - start_time
        duration_ms = int(duration_seconds * 1000)
        # Expose timing to clients for easy measurement
        response.headers["X-Process-Time"] = f"{duration_seconds:.6f}"
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        # Log concise structured line for server-side analysis (no special formatter needed)
        timing_logger.info(
            f"request_completed method={method} path={path} status_code={status_code} duration_ms={duration_ms}"
        )
        return response
    except Exception:
        duration_seconds = time.perf_counter() - start_time
        duration_ms = int(duration_seconds * 1000)
        timing_logger.exception(
            f"request_failed method={method} path={path} status_code=500 duration_ms={duration_ms}"
        )
        raise


@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(topics_router.router)
app.include_router(questions_router.router)
app.include_router(streak_router.router)
app.include_router(generate_router.router)


