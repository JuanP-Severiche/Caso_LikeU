from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

import pandas as pd

from src.classifier import classify_incoming_message


ID_COLUMNS = {
    "id",
    "account_id",
    "inbox_id",
    "conversation_id",
    "sender_id",
    "contact_id",
    "sistema_lead_id",
    "conversation_display_id",
    "id_sistema",
    "id_db_externa",
    "id_leads_db_externa",
}

DATE_COLUMNS = ("created_at", "updated_at")


MOJIBAKE_MARKERS = (
    "Ã",
    "Â",
    "â€",
    "â€™",
    "â€œ",
    "â€",
    "ðŸ",
    "ï¿½",
    "�",
)


def _suspicious_text_score(text: str) -> int:
    """Puntúa señales típicas de UTF-8 interpretado como Latin-1/Windows-1252."""
    return sum(text.count(marker) for marker in MOJIBAKE_MARKERS)


def repair_mojibake(value: object) -> tuple[str, bool]:
    """
    Corrige mojibake recuperable sin recodificar toda la cadena.

    Se reparan secuencias conocidas producidas cuando caracteres UTF-8 en español
    fueron interpretados como Latin-1/Windows-1252. La estrategia por reemplazo
    puntual evita dañar caracteres que ya estén correctos dentro del mismo mensaje.
    """
    text = "" if value is None else unicodedata.normalize("NFC", str(value))
    if not text:
        return text, False

    # Mapa generado a partir de caracteres relevantes para español.
    intended_chars = "áéíóúÁÉÍÓÚñÑüÜ¿¡"
    replacements = {
        char.encode("utf-8").decode("latin-1"): char
        for char in intended_chars
    }

    # Secuencias frecuentes adicionales de Windows-1252/UTF-8.
    replacements.update({
        "Â ": " ",
        "Â¿": "¿",
        "Â¡": "¡",
        "â€™": "’",
        "â€œ": "“",
        "â€": "”",
        "â€“": "–",
        "â€”": "—",
        "â€¦": "…",
    })

    repaired = text
    for bad, good in replacements.items():
        repaired = repaired.replace(bad, good)

    repaired = unicodedata.normalize("NFC", repaired)
    return repaired, repaired != text


def normalize_message_text(value: object) -> tuple[str, bool, str]:
    """
    Genera el mensaje limpio sin destruir el dato fuente.

    - normaliza Unicode a NFC;
    - repara mojibake recuperable (ej. conversaciÃ³n -> conversación);
    - convierte el marcador ¶ en espacios;
    - compacta espacios y saltos de línea;
    - conserva signos, tildes, ñ, emojis y contenido semántico;
    - marca pérdidas ya presentes en la fuente como Nu?Ez sin inventar caracteres.
    """
    repaired, was_repaired = repair_mojibake(value)
    cleaned = repaired.replace("¶", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = unicodedata.normalize("NFC", cleaned)

    # Señal conservadora de carácter ya perdido en origen: letra ? letra.
    unrecoverable = bool(
        re.search(r"(?<=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])\?(?=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])", cleaned)
    )

    if unrecoverable:
        quality = "SOURCE_CHARACTER_LOSS"
    elif was_repaired:
        quality = "ENCODING_REPAIRED"
    else:
        quality = "OK"

    return cleaned, was_repaired, quality


def _clean_cell(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _is_separator_row(value: object) -> bool:
    text = _clean_cell(value)
    return bool(text) and set(text) == {"-"}


def normalize_identifier(value: object) -> int | None:
    text = _clean_cell(value)
    if not text:
        return None

    # Source identifiers use dots as thousands separators (e.g. 31.888 -> 31888).
    compact = text.replace(".", "")
    return int(compact) if compact.isdigit() else None


def parse_embedded_json(value: object) -> dict[str, Any]:
    """Parse JSON stored as an escaped JSON string; invalid/empty values return {}."""
    text = _clean_cell(value)
    if not text:
        return {}

    candidates = [text]
    if len(text) >= 2 and text[0] == text[-1] == '"':
        candidates.append(text[1:-1])

    for candidate in candidates:
        current: Any = candidate
        for _ in range(2):
            if isinstance(current, dict):
                return current
            if not isinstance(current, str):
                break
            try:
                current = json.loads(current)
            except (json.JSONDecodeError, TypeError):
                # The file stores escaped quotes after an outer quote layer.
                try:
                    current = json.loads(current.replace('\\"', '"'))
                except (json.JSONDecodeError, TypeError):
                    break
        if isinstance(current, dict):
            return current

    return {}


def _extract_external_error(row: pd.Series) -> str | None:
    for column in ("content_attributes", "content"):
        parsed = parse_embedded_json(row.get(column, ""))
        value = parsed.get("external_error")
        if value:
            return str(value).strip()
    return None


def _extract_template_name(row: pd.Series) -> str | None:
    for column in ("additional_attributes", "content_attributes", "content"):
        parsed = parse_embedded_json(row.get(column, ""))

        template_params = parsed.get("template_params")
        if isinstance(template_params, dict) and template_params.get("name"):
            return str(template_params["name"]).strip()

        if parsed.get("template_name"):
            return str(parsed["template_name"]).strip()

        if parsed.get("name") and "template" in column:
            return str(parsed["name"]).strip()

    return None


def _json_parse_status(row: pd.Series) -> str:
    json_fields = ("content_attributes", "additional_attributes")
    populated = [field for field in json_fields if _clean_cell(row.get(field, "")) not in ("", '"{}"', "{}")]
    if not populated:
        return "EMPTY"
    return "OK" if any(parse_embedded_json(row.get(field, "")) for field in populated) else "INVALID"


def clean_messages(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data.columns = [column.strip().lower() for column in data.columns]

    for column in data.columns:
        data[column] = data[column].map(_clean_cell)

    if "id" not in data.columns:
        raise ValueError("El archivo no contiene la columna obligatoria 'id'.")

    data = data.loc[~data["id"].map(_is_separator_row)].copy()

    empty_columns = [column for column in data.columns if (data[column] == "").all()]
    if empty_columns:
        data = data.drop(columns=empty_columns)

    for column in ID_COLUMNS.intersection(data.columns):
        data[column] = data[column].map(normalize_identifier).astype("Int64")

    for column in DATE_COLUMNS:
        if column in data.columns:
            data[column] = pd.to_datetime(data[column], errors="coerce")

    if "private" in data.columns:
        data["private"] = data["private"].str.lower().map({"true": True, "false": False}).astype("boolean")

    data["external_error"] = data.apply(_extract_external_error, axis=1)
    data["template_name"] = data.apply(_extract_template_name, axis=1)
    data["json_parse_status"] = data.apply(_json_parse_status, axis=1)

    # Se conserva content como dato fuente y se crea una versión limpia para consumo analítico.
    normalized_content = data.get("content", pd.Series(index=data.index, dtype=str)).map(normalize_message_text)
    normalized_frame = pd.DataFrame(
        normalized_content.tolist(),
        columns=["clean_message", "encoding_repaired", "text_quality_status"],
        index=data.index,
    )
    data[["clean_message", "encoding_repaired", "text_quality_status"]] = normalized_frame

    classified = data.apply(
        lambda row: classify_incoming_message(row.get("message_type", ""), row.get("clean_message", "")),
        axis=1,
        result_type="expand",
    )
    classified.columns = ["incoming_category", "matched_keyword"]
    data[["incoming_category", "matched_keyword"]] = classified

    data["content_is_empty"] = data.get("content", pd.Series(index=data.index, dtype=str)).eq("")

    return data.reset_index(drop=True)
