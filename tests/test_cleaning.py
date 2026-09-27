from __future__ import annotations

import pandas as pd

from src.transform import clean_messages, normalize_identifier, normalize_message_text, repair_mojibake


def test_normalize_identifier_removes_thousands_separator() -> None:
    assert normalize_identifier("31.888") == 31888
    assert normalize_identifier("2.460") == 2460
    assert normalize_identifier("") is None


def test_clean_messages_removes_separator_row() -> None:
    frame = pd.DataFrame(
        {
            "id": ["------", "31.888"],
            "content": ["------", " Hola "],
            "conversation_id": ["------", "2.460"],
            "message_type": ["------------", "incoming"],
            "created_at": ["----------------", "2023-07-28 14:27:58.000"],
            "updated_at": ["----------------", "2023-07-28 14:27:58.000"],
            "private": ["-------", "false"],
            "status": ["---------", "sent"],
            "content_attributes": ["----", '"{}"'],
            "additional_attributes": ["----", '"{}"'],
        }
    )

    result = clean_messages(frame)

    assert len(result) == 1
    assert result.iloc[0]["id"] == 31888
    assert result.iloc[0]["conversation_id"] == 2460
    assert result.iloc[0]["content"] == "Hola"


def test_repair_mojibake_restores_utf8_text_without_touching_valid_spanish() -> None:
    repaired, changed = repair_mojibake("La conversaci\u00c3\u00b3n fue marcada")
    assert repaired == "La conversación fue marcada"
    assert changed is True

    valid, changed = repair_mojibake("Información, asesoría y niño")
    assert valid == "Información, asesoría y niño"
    assert changed is False


def test_clean_message_preserves_semantics_and_flags_source_loss() -> None:
    cleaned, repaired, quality = normalize_message_text("Hola\u00b6La conversaci\u00c3\u00b3n continúa")
    assert cleaned == "Hola La conversación continúa"
    assert repaired is True
    assert quality == "ENCODING_REPAIRED"

    cleaned, repaired, quality = normalize_message_text("Ana Nu?Ez")
    assert cleaned == "Ana Nu?Ez"
    assert repaired is False
    assert quality == "SOURCE_CHARACTER_LOSS"


def test_clean_messages_keeps_original_content_and_adds_clean_message() -> None:
    frame = pd.DataFrame(
        {
            "id": ["31.888"],
            "content": [" La conversaci\u00c3\u00b3n fue marcada\u00b6por Rojas bpo "],
            "conversation_id": ["2.460"],
            "message_type": ["activity"],
            "created_at": ["2023-07-28 14:27:58.000"],
            "updated_at": ["2023-07-28 14:27:58.000"],
            "private": ["false"],
            "status": ["sent"],
            "content_attributes": ['"{}"'],
            "additional_attributes": ['"{}"'],
        }
    )

    result = clean_messages(frame)

    assert result.iloc[0]["content"] == "La conversaci\u00c3\u00b3n fue marcada\u00b6por Rojas bpo"
    assert result.iloc[0]["clean_message"] == "La conversación fue marcada por Rojas bpo"
    assert bool(result.iloc[0]["encoding_repaired"]) is True
    assert result.iloc[0]["text_quality_status"] == "ENCODING_REPAIRED"
