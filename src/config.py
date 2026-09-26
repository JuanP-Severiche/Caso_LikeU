from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    raw_file: Path = Path(os.getenv("RAW_FILE", "data/raw/prueba.txt"))
    processed_file: Path = Path(
        os.getenv("PROCESSED_FILE", "data/processed/messages_clean.csv")
    )
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://likeu_user:likeu_local_password@localhost:5432/likeu_analytics",
    )
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()


settings = Settings()
