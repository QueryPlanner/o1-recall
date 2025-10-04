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
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    allowed_origins: List[str] = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

    settings = {
        "DATABASE_URL": database_url,
        "ALLOWED_ORIGINS": allowed_origins,
        "GENAI_API_KEY": os.getenv("GENAI_API_KEY", ""),
        "GENAI_MODEL": os.getenv("GENAI_MODEL", "gemini-2.0-flash-001"),
        "DEFAULT_USER_ID": int(os.getenv("DEFAULT_USER_ID", "1")),
    }
    return settings


