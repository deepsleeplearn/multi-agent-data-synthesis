from __future__ import annotations

from multi_agent_data_synthesis.schemas import DialogueSample, Scenario, effective_required_slots


def validate_dialogue(sample: DialogueSample) -> dict:
    issues = []

    if not sample.transcript:
        issues.append("transcript is empty")
    elif sample.transcript[0].speaker != "service":
        issues.append("dialogue must start with service")

    expected = "service"
    for turn in sample.transcript:
        if turn.speaker != expected:
            issues.append(f"speaker order mismatch at round {turn.round_index}: expected {expected}")
            break
        expected = "user" if expected == "service" else "service"

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
