from __future__ import annotations

import json
from pathlib import Path

from multi_agent_data_synthesis.schemas import DialogueSample


def write_jsonl(samples: list[DialogueSample], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for sample in samples:
            handle.write(json.dumps(sample.to_dict(), ensure_ascii=False) + "\n")


def write_json(samples: list[DialogueSample], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([sample.to_dict() for sample in samples], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
