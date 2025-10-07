import os
from typing import List

from dotenv import load_dotenv


def load_settings() -> dict:
    load_dotenv()

    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required in environment")

    allowed_origins_raw = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:5173",
    )
    allowed_origins: List[str] = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

    # Parse multiple API keys from GENAI_API_KEYS, fallback to single GENAI_API_KEY
    api_keys_raw = os.getenv("GENAI_API_KEYS", "")
    api_keys: List[str] = [k.strip() for k in api_keys_raw.split(",") if k.strip()]
    if not api_keys:
        single_key = os.getenv("GENAI_API_KEY", "").strip()
        if single_key:
            api_keys = [single_key]

    # Models: support two explicit models, defaulting to the previous single model env
    legacy_model = os.getenv("GENAI_MODEL", "gemini-2.5-flash").strip()
    model_1 = os.getenv("GEN_AI_MODEL_1", legacy_model).strip()
    model_2 = os.getenv("GEN_AI_MODEL_2", legacy_model).strip()

    settings = {
        "DATABASE_URL": database_url,
        "ALLOWED_ORIGINS": allowed_origins,
        # Keep legacy single key for backward-compat while preferring the list
        "GENAI_API_KEY": os.getenv("GENAI_API_KEY", ""),
        "GENAI_API_KEYS": api_keys,
        # Keep legacy single model for backward-compat while preferring the pair
        "GENAI_MODEL": legacy_model,
        "GEN_AI_MODEL_1": model_1,
        "GEN_AI_MODEL_2": model_2,
        "DEFAULT_USER_ID": int(os.getenv("DEFAULT_USER_ID", "1")),
    }
    return settings


