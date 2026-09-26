from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


TABLE_NAME = "messages"


def build_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True, future=True)


def load_messages(frame: pd.DataFrame, database_url: str) -> None:
    engine = build_engine(database_url)

    with engine.begin() as connection:
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
