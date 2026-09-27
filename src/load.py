"""Carga del DataFrame procesado en PostgreSQL."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


TABLE_NAME = "messages"


def build_engine(database_url: str) -> Engine:
    """Crea el engine SQLAlchemy usado por la carga."""
    return create_engine(database_url, pool_pre_ping=True, future=True)


def load_messages(frame: pd.DataFrame, database_url: str) -> None:
    """Reemplaza el contenido de messages y actualiza estadisticas del optimizador."""
    engine = build_engine(database_url)

    with engine.begin() as connection:
        # Mantiene compatibilidad con bases creadas antes de agregar las columnas de calidad.
        connection.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS clean_message TEXT"))
        connection.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS encoding_repaired BOOLEAN NOT NULL DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS text_quality_status VARCHAR(40)"))
        connection.execute(text("TRUNCATE TABLE messages RESTART IDENTITY"))

    frame.to_sql(
        TABLE_NAME,
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500,
    )

    with engine.begin() as connection:
        connection.execute(text("ANALYZE messages"))
