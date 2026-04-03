from __future__ import annotations

from multi_agent_data_synthesis.schemas import (
    DialogueSample,
    Scenario,
    SERVICE_SPEAKER,
    USER_SPEAKER,
    effective_required_slots,
    normalize_speaker,
)


def validate_dialogue(sample: DialogueSample) -> dict:
    issues = []

    if not sample.transcript:
        issues.append("transcript is empty")
    else:
        first_speaker = normalize_speaker(sample.transcript[0].speaker)
        if first_speaker not in {SERVICE_SPEAKER, USER_SPEAKER}:
            issues.append("dialogue must start with user or service")
        else:
            expected = first_speaker
            for turn in sample.transcript:
                if normalize_speaker(turn.speaker) != expected:
                    issues.append(
                        f"speaker order mismatch at round {turn.round_index}: expected {expected}"
                    )
                    break
                expected = USER_SPEAKER if expected == SERVICE_SPEAKER else SERVICE_SPEAKER

    required_slots: list[str] | None = None
    if sample.scenario:
        try:
            scenario = Scenario.from_dict(sample.scenario)
            required_slots = effective_required_slots(scenario)
        except (KeyError, TypeError, ValueError):
            required_slots = None
    if required_slots is None:
        missing_required = [slot for slot in sample.missing_slots if not sample.collected_slots.get(slot)]
    else:
        missing_required = [slot for slot in required_slots if not sample.collected_slots.get(slot)]
    if missing_required and sample.status == "completed":
        issues.append("status marked completed but required slots are still missing")

    return {
        "passed": not issues,
        "issues": issues,
        "required_slots_complete": not missing_required,
    }
