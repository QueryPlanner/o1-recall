# Backend - FastAPI

## Environment
Create `.env` in `backend/`:
```
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DB_NAME?sslmode=require
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DEFAULT_USER_ID=1

# Multiple API keys supported (comma-separated). One is chosen randomly per request
GENAI_API_KEYS=key1,key2,key3

# Two-model strategy: use model 1; on overload (503/UNAVAILABLE) fallback to model 2
GEN_AI_MODEL_1=gemini-2.0-flash-001
GEN_AI_MODEL_2=gemini-2.0-pro
```

Backward compatibility:
- If `GENAI_API_KEYS` is not set, `GENAI_API_KEY` (single key) is used.
- If `GEN_AI_MODEL_1/2` are not set, `GENAI_MODEL` is used for both.

## Run locally
```
uv venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Generation behavior
- API key rotation: each generation request randomly selects a key from `GENAI_API_KEYS`.
- Model fallback: attempts `GEN_AI_MODEL_1`; on `google.genai.errors.ServerError` with code 503 or status `UNAVAILABLE`, retries once with `GEN_AI_MODEL_2`.

## Endpoints
- POST `/generate/from-link` (form): `url`, `size`, `topic?`, `sub_topic?`
- POST `/generate/from-pdf` (multipart): `pdf`, `size`, `topic?`, `sub_topic?`
- See more in the root README.
