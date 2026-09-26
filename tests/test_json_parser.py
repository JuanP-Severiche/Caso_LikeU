from __future__ import annotations

import pandas as pd

from src.transform import clean_messages, parse_embedded_json


def test_parse_escaped_json_string() -> None:
    raw = '"{\\"external_error\\": \\"(#132000) Number of parameters does not match\\"}"'
    parsed = parse_embedded_json(raw)
    assert parsed["external_error"].startswith("(#132000)")


def test_extracts_error_and_template_from_real_layout() -> None:
    frame = pd.DataFrame(
        {
            "id": ["35.098"],
            "content": ["mensaje"],
            "conversation_id": ["7.226"],
            "message_type": ["outgoing"],
            "created_at": ["2023-07-29 13:43:11.000"],
            "updated_at": ["2023-07-29 13:43:12.000"],
            "private": ["false"],
            "status": ["failed"],
            "content_attributes": [
                '"{\\"external_error\\": \\"(#132000) Number of parameters does not match the expected number of params\\"}"'
            ],
            "additional_attributes": [
                '"{\\"template_params\\": {\\"name\\": \\"lanzamiento_\\", \\"category\\": \\"MARKETING\\"}}"'
            ],
        }
    )

    result = clean_messages(frame)

    assert result.iloc[0]["external_error"].startswith("(#132000)")
    assert result.iloc[0]["template_name"] == "lanzamiento_"
    assert result.iloc[0]["json_parse_status"] == "OK"
