from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "evals"
SPLITS = ("train", "dev", "test", "test_round2")


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.lower())


def _load_split(name: str) -> list[dict]:
    path = EVAL_DIR / f"agent_{name}.jsonl"
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        for field in ("id", "topic", "question", "expected_intent"):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"{path.name}:{line_number} missing {field}")
        rows.append(row)
    if not rows:
        raise ValueError(f"{path.name} is empty")
    return rows


def validate_splits() -> dict[str, int]:
    loaded = {name: _load_split(name) for name in SPLITS}
    for field, transform in (
        ("id", lambda row: row["id"]),
        ("topic", lambda row: _normalize(row["topic"])),
        ("question", lambda row: _normalize(row["question"])),
    ):
        owners: dict[str, str] = {}
        for split, rows in loaded.items():
            for row in rows:
                value = transform(row)
                previous = owners.get(value)
                if previous and previous != split:
                    raise ValueError(f"{field} leakage between {previous} and {split}: {value}")
                owners[value] = split
    return {name: len(rows) for name, rows in loaded.items()}


if __name__ == "__main__":
    counts = validate_splits()
    print("PASS agent eval split isolation: " + ", ".join(f"{name}={count}" for name, count in counts.items()))
