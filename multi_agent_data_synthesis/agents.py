from __future__ import annotations

from typing import Any

from multi_agent_data_synthesis.dialogue_plans import resolve_second_round_reply_strategy
from multi_agent_data_synthesis.llm import OpenAIChatClient
from multi_agent_data_synthesis.prompts import build_user_agent_messages
from multi_agent_data_synthesis.schemas import DialogueTurn, Scenario
from multi_agent_data_synthesis.service_policy import (
    ServiceDialoguePolicy,
    ServiceRuntimeState,
)


class UserAgent:
    def __init__(
        self,
        client: OpenAIChatClient,
        model: str,
        temperature: float,
        second_round_include_issue_probability: float,
    ):
        self.client = client
        self.model = model
        self.temperature = temperature
        self.second_round_include_issue_probability = second_round_include_issue_probability

    def respond(
        self,
        *,
        scenario: Scenario,
        transcript: list[DialogueTurn],
        round_index: int,
    ) -> dict[str, Any]:
        second_round_reply_strategy = resolve_second_round_reply_strategy(
            scenario_id=scenario.scenario_id,
            hidden_context=scenario.hidden_context,
            include_issue_probability=self.second_round_include_issue_probability,
        )
        payload = self.client.complete_json(
            model=self.model,
            messages=build_user_agent_messages(
                scenario,
                transcript,
                round_index,
                second_round_reply_strategy=second_round_reply_strategy,
            ),
            temperature=self.temperature,
        )
        return {
            "reply": str(payload.get("reply", "")).strip(),
            "call_complete": bool(payload.get("call_complete", False)),
        }

    async def respond_async(
        self,
        *,
        scenario: Scenario,
        transcript: list[DialogueTurn],
        round_index: int,
    ) -> dict[str, Any]:
        second_round_reply_strategy = resolve_second_round_reply_strategy(
            scenario_id=scenario.scenario_id,
            hidden_context=scenario.hidden_context,
            include_issue_probability=self.second_round_include_issue_probability,
        )
        payload = await self.client.complete_json_async(
            model=self.model,
            messages=build_user_agent_messages(
                scenario,
                transcript,
                round_index,
                second_round_reply_strategy=second_round_reply_strategy,
            ),
            temperature=self.temperature,
        )
        return {
            "reply": str(payload.get("reply", "")).strip(),
            "call_complete": bool(payload.get("call_complete", False)),
        }


class ServiceAgent:
    def __init__(
        self,
        client: OpenAIChatClient,
        model: str,
        temperature: float,
        ok_prefix_probability: float = 1.0,
    ):
        self.policy = ServiceDialoguePolicy(ok_prefix_probability=ok_prefix_probability)

    def respond(
        self,
        *,
        scenario: Scenario,
        transcript: list[DialogueTurn],
        collected_slots: dict[str, str],
        runtime_state: ServiceRuntimeState,
    ) -> dict[str, Any]:
        result = self.policy.respond(
            scenario=scenario,
            transcript=transcript,
            collected_slots=collected_slots,
            runtime_state=runtime_state,
        )
        return {
            "reply": result.reply,
            "slot_updates": result.slot_updates,
            "is_ready_to_close": result.is_ready_to_close,
        }

    def build_initial_user_utterance(self, scenario: Scenario) -> str:
        return self.policy.build_initial_user_utterance(scenario)
