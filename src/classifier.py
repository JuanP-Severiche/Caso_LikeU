from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable


CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Queja": (
        "inconforme",
        "no llego",
        "no me llego",
        "me cobraron",
        "me cobra",
        "mal servicio",
        "problema",
        "reclamo",
        "queja",
        "devolucion",
        "faltante",
        "no funciona",
    ),
    "Pedido": (
        "pedido",
        "pedir",
        "comprar",
        "compra",
        "catalogo",
        "producto",
        "ingresarlo",
        "factura",
    ),
    "Soporte": (
        "ayuda",
        "soporte",
        "asesoria",
        "asesoría",
        "llamada",
        "plataforma",
        "codigo",
        "código",
        "clave",
        "ingresar",
        "error",
        "duda",
    ),
}


def normalize_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _first_match(text: str, keywords: Iterable[str]) -> str | None:
    for keyword in keywords:
        normalized_keyword = normalize_text(keyword)
        if normalized_keyword in text:
            return keyword
    return None


def classify_incoming_message(message_type: str, content: str) -> tuple[str | None, str | None]:
    if str(message_type).strip().lower() != "incoming":
        return None, None

    normalized = normalize_text(content)
    if not normalized:
        return "Otros", None

    # Queja has priority because it often also contains words such as "pedido" or "factura".
    for category in ("Queja", "Pedido", "Soporte"):
        keyword = _first_match(normalized, CATEGORY_KEYWORDS[category])
        if keyword:
            return category, keyword

    return "Otros", None
