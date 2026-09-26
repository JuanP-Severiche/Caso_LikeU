from __future__ import annotations

from src.classifier import classify_incoming_message, normalize_text


def test_normalize_text_removes_accents_and_extra_spaces() -> None:
    assert normalize_text("  Necesito   asesoría  ") == "necesito asesoria"


def test_complaint_has_priority_over_order_keyword() -> None:
    category, keyword = classify_incoming_message(
        "incoming", "Estoy inconforme con un premio que pedí y me lo están cobrando"
    )
    assert category == "Queja"
    assert keyword is not None


def test_order_classification() -> None:
    category, _ = classify_incoming_message("incoming", "No me dejes sin pedido porfis")
    assert category == "Pedido"


def test_non_incoming_is_not_classified() -> None:
    assert classify_incoming_message("outgoing", "pedido") == (None, None)
