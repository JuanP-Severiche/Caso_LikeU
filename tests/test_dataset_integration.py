from __future__ import annotations

from pathlib import Path

from src.extract import read_raw_messages
from src.transform import clean_messages


def test_provided_dataset_expected_shape_and_counts() -> None:
    path = Path("data/raw/prueba.txt")
    if not path.exists():
        return

    result = clean_messages(read_raw_messages(path))

    assert len(result) == 3687
    assert result["id"].duplicated().sum() == 0
    assert result["conversation_id"].nunique() == 2153
    assert (result["message_type"] == "incoming").sum() == 430
    assert (result["message_type"] == "outgoing").sum() == 2507
    assert ((result["message_type"] == "outgoing") & (result["status"] == "failed")).sum() == 1396
