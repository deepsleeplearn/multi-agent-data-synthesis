from __future__ import annotations

import json
from pathlib import Path

from multi_agent_data_synthesis.schemas import Scenario


class ScenarioFactory:
    def load_from_file(self, path: Path) -> list[Scenario]:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("Scenario file must contain a JSON array.")
        scenarios = [Scenario.from_dict(item) for item in raw]
        if not scenarios:
            raise ValueError("Scenario file is empty.")
        return scenarios

    def expand_to_count(self, scenarios: list[Scenario], count: int | None) -> list[Scenario]:
        if count is None or count <= len(scenarios):
            return scenarios if count is None else scenarios[:count]

        expanded: list[Scenario] = []
        for index in range(count):
            base = scenarios[index % len(scenarios)]
            expanded.append(base.clone_with_id(f"{base.scenario_id}_sample_{index + 1:04d}"))
        return expanded
