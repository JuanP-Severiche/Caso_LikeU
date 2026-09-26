from __future__ import annotations

import pandas as pd

from src.transform import clean_messages, normalize_identifier


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
