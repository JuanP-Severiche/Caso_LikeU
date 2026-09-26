from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


def read_raw_messages(path: Path) -> pd.DataFrame:
    """Read the source TXT without interpreting escaped JSON quotes as CSV quotes."""
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de entrada: {path}")

    frame = pd.read_csv(
        path,
        sep="|",
        dtype=str,
        keep_default_na=False,
        engine="python",
        quoting=csv.QUOTE_NONE,
    )

    frame.columns = [column.strip() for column in frame.columns]

    edge_columns = [
        column for column in frame.columns if not column or column.startswith("Unnamed:")
    ]
    if edge_columns:
        frame = frame.drop(columns=edge_columns)

    return frame
