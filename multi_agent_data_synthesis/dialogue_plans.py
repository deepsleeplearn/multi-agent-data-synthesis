from __future__ import annotations

import hashlib
from typing import Any


SECOND_ROUND_REPLY_CONFIRM_ONLY = "confirm_only"
SECOND_ROUND_REPLY_CONFIRM_WITH_ISSUE = "confirm_with_issue"


def normalize_second_round_reply_strategy(value: Any) -> str:
    normalized = str(value or "").strip()
    if normalized == SECOND_ROUND_REPLY_CONFIRM_WITH_ISSUE:
        return SECOND_ROUND_REPLY_CONFIRM_WITH_ISSUE
    return SECOND_ROUND_REPLY_CONFIRM_ONLY


def decide_second_round_reply_strategy(
    scenario_id: str,
    include_issue_probability: float,
) -> str:
    probability = max(0.0, min(1.0, float(include_issue_probability)))
    digest = hashlib.sha256(f"{scenario_id}:second_round_include_issue".encode("utf-8")).digest()
    score = int.from_bytes(digest[:8], byteorder="big", signed=False) / 2**64
    if score < probability:
        return SECOND_ROUND_REPLY_CONFIRM_WITH_ISSUE
    return SECOND_ROUND_REPLY_CONFIRM_ONLY


def resolve_second_round_reply_strategy(
    *,
    scenario_id: str,
    hidden_context: dict[str, Any] | None,
    include_issue_probability: float,
) -> str:
    hidden_context = hidden_context or {}
    strategy = hidden_context.get("second_round_reply_strategy", "")
    if str(strategy).strip():
        return normalize_second_round_reply_strategy(strategy)
    return decide_second_round_reply_strategy(scenario_id, include_issue_probability)
