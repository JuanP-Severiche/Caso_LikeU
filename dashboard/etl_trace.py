from __future__ import annotations

import csv
import inspect
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.classifier import classify_incoming_message
from src.extract import read_raw_messages
from src.load import load_messages
from src.transform import clean_messages, normalize_message_text, parse_embedded_json, repair_mojibake


RAW_FILE = Path(os.getenv("RAW_FILE", "data/raw/prueba.txt"))
PROCESSED_FILE = Path(os.getenv("PROCESSED_FILE", "data/processed/messages_clean.csv"))

RAW_PREVIEW_COLUMNS = [
    "id",
    "content",
    "conversation_id",
    "message_type",
    "created_at",
    "status",
    "content_attributes",
    "additional_attributes",
]

PROCESSED_PREVIEW_COLUMNS = [
    "id",
    "message_type",
    "status",
    "content",
    "clean_message",
    "encoding_repaired",
    "text_quality_status",
    "external_error",
    "template_name",
    "incoming_category",
]


def _human_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{value:.1f} GB"


def _file_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "name": path.name,
            "exists": False,
            "size_bytes": 0,
            "size": "0 B",
            "modified_at": None,
        }

    stat = path.stat()
    return {
        "path": str(path),
        "name": path.name,
        "exists": True,
        "size_bytes": stat.st_size,
        "size": _human_size(stat.st_size),
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def _truncate(value: Any, limit: int = 130) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _frame_payload(frame: pd.DataFrame, preferred_columns: list[str]) -> dict[str, Any]:
    if frame.empty:
        return {"columns": [], "rows": []}

    columns = [column for column in preferred_columns if column in frame.columns]
    if not columns:
        columns = list(frame.columns[:8])

    preview = frame.loc[:, columns].copy()
    rows: list[dict[str, str]] = []
    for record in preview.to_dict(orient="records"):
        rows.append({key: _truncate(value) for key, value in record.items()})
    return {"columns": columns, "rows": rows}


def preview_raw(limit: int = 6) -> dict[str, Any]:
    if not RAW_FILE.exists():
        return {"columns": [], "rows": []}

    frame = pd.read_csv(
        RAW_FILE,
        sep="|",
        dtype=str,
        keep_default_na=False,
        engine="python",
        quoting=csv.QUOTE_NONE,
        nrows=max(limit + 1, 8),
    )
    frame.columns = [column.strip() for column in frame.columns]
    edge_columns = [column for column in frame.columns if not column or column.startswith("Unnamed:")]
    if edge_columns:
        frame = frame.drop(columns=edge_columns)
    if "id" in frame.columns:
        separator = frame["id"].astype(str).str.strip().str.fullmatch(r"-+")
        frame = frame.loc[~separator]
    return _frame_payload(frame.head(limit), RAW_PREVIEW_COLUMNS)


def preview_processed(limit: int = 8) -> dict[str, Any]:
    if not PROCESSED_FILE.exists():
        return {"columns": [], "rows": []}
    frame = pd.read_csv(PROCESSED_FILE, nrows=limit, keep_default_na=False, encoding="utf-8-sig")
    return _frame_payload(frame, PROCESSED_PREVIEW_COLUMNS)


def count_data_rows(path: Path, subtract_header: bool = True) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        count = sum(1 for _ in handle)
    if subtract_header and count:
        count -= 1
    return max(count, 0)



def processed_text_quality() -> dict[str, int]:
    if not PROCESSED_FILE.exists():
        return {"records": 0, "encoding_repaired": 0, "source_character_loss": 0, "ok": 0}

    frame = pd.read_csv(
        PROCESSED_FILE,
        usecols=lambda column: column in {"encoding_repaired", "text_quality_status"},
        keep_default_na=False,
        encoding="utf-8-sig",
    )
    if frame.empty:
        return {"records": 0, "encoding_repaired": 0, "source_character_loss": 0, "ok": 0}

    repaired = frame.get("encoding_repaired", pd.Series(dtype=str)).astype(str).str.lower().eq("true").sum()
    status = frame.get("text_quality_status", pd.Series(dtype=str)).astype(str)
    return {
        "records": int(len(frame)),
        "encoding_repaired": int(repaired),
        "source_character_loss": int(status.eq("SOURCE_CHARACTER_LOSS").sum()),
        "ok": int(status.eq("OK").sum()),
    }


def source_code_support() -> list[dict[str, str]]:
    return [
        {
            "id": "extract",
            "title": "1. Lectura del TXT y delimitador",
            "description": "Lee prueba.txt con separador | sin interpretar como CSV las comillas escapadas del JSON.",
            "language": "python",
            "code": inspect.getsource(read_raw_messages).strip(),
        },
        {
            "id": "transform",
            "title": "2. Limpieza y enriquecimiento",
            "description": "Normaliza columnas, IDs, fechas, booleanos, elimina separadores y crea campos derivados.",
            "language": "python",
            "code": inspect.getsource(clean_messages).strip(),
        },
        {
            "id": "text-quality",
            "title": "3. Normalización del mensaje",
            "description": "Conserva content original y crea clean_message con Unicode NFC, reparación conservadora de mojibake y bandera de calidad.",
            "language": "python",
            "code": (
                inspect.getsource(repair_mojibake).strip()
                + "\n\n"
                + inspect.getsource(normalize_message_text).strip()
            ),
        },
        {
            "id": "json",
            "title": "4. Parsing del JSON embebido",
            "description": "Tolera el JSON escapado y lo convierte a estructuras Python para extraer errores y plantillas.",
            "language": "python",
            "code": inspect.getsource(parse_embedded_json).strip(),
        },
        {
            "id": "nlp",
            "title": "5. NLP ligero por palabras clave",
            "description": "Clasifica incoming con reglas explícitas y auditables, sin modelos externos.",
            "language": "python",
            "code": inspect.getsource(classify_incoming_message).strip(),
        },
        {
            "id": "load",
            "title": "6. Persistencia en PostgreSQL",
            "description": "Carga el DataFrame limpio por lotes y actualiza estadísticas para el optimizador.",
            "language": "python",
            "code": inspect.getsource(load_messages).strip(),
        },
    ]


def get_etl_trace() -> dict[str, Any]:
    raw_meta = _file_metadata(RAW_FILE)
    processed_meta = _file_metadata(PROCESSED_FILE)

    raw_meta["rows_on_disk"] = count_data_rows(RAW_FILE, subtract_header=True)
    processed_meta["rows_on_disk"] = count_data_rows(PROCESSED_FILE, subtract_header=True)

    return {
        "raw": raw_meta,
        "processed": processed_meta,
        "raw_preview": preview_raw(),
        "processed_preview": preview_processed(),
        "text_quality": processed_text_quality(),
        "steps": [
            {"number": 1, "label": "TXT crudo", "detail": "Archivo fuente delimitado por |"},
            {"number": 2, "label": "Limpieza", "detail": "Estructura, IDs, fechas, espacios y columnas vacías"},
            {"number": 3, "label": "Texto", "detail": "Unicode NFC + reparación conservadora de mojibake"},
            {"number": 4, "label": "JSON", "detail": "external_error y template_name"},
            {"number": 5, "label": "NLP ligero", "detail": "Pedido, Queja, Soporte u Otros"},
            {"number": 6, "label": "CSV limpio", "detail": "UTF-8 con BOM + clean_message + banderas de calidad"},
            {"number": 7, "label": "PostgreSQL", "detail": "Tabla messages + vistas + índices"},
            {"number": 8, "label": "Dashboard", "detail": "SQL parametrizado y visualización interactiva"},
        ],
        "code_support": source_code_support(),
    }
