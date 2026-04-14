from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from multi_agent_data_synthesis.cli import (
    _hydrate_manual_test_scenario_locally,
    _manual_test_requires_generated_hidden_settings,
    build_parser,
)
from multi_agent_data_synthesis.orchestrator import DialogueOrchestrator
from tests.test_orchestrator import build_scenario
from tests.test_manual_test import build_scenario_payload
from multi_agent_data_synthesis.schemas import Scenario


class CliTests(unittest.TestCase):
    def test_generate_parser_accepts_show_persona_flag(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "generate",
                "--count",
                "1",
                "--show-dialogue",
                "--show-persona",
            ]
        )

        self.assertTrue(args.show_dialogue)
        self.assertTrue(args.show_persona)

    def test_dialogue_header_can_include_persona_profile(self):
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            DialogueOrchestrator._print_dialogue_header(
                build_scenario(),
                show_persona_profile=True,
            )

        output = buffer.getvalue()
        self.assertIn("Persona: 普通用户", output)
        self.assertIn("Speech Style: 简洁", output)

    def test_manual_test_requires_generated_hidden_settings_for_placeholder_seed(self):
        scenario = Scenario.from_dict(
            {
                "scenario_id": "seed_case",
                "product": {
                    "brand": "美的",
                    "category": "空气能热水器",
                    "model": "KF66/200L-MI(E4)",
                    "purchase_channel": "京东官方旗舰店",
                },
                "customer": {
                    "full_name": "未知",
                    "surname": "未知",
                    "phone": "未知",
                    "address": "未知",
                    "persona": "未知",
                    "speech_style": "未知",
                },
                "request": {
                    "request_type": "fault",
                    "issue": "未知",
                    "desired_resolution": "未知",
                    "availability": "未知",
                },
                "hidden_context": {},
                "required_slots": ["issue_description", "surname", "phone", "address", "request_type"],
                "max_turns": 20,
            }
        )

        self.assertTrue(_manual_test_requires_generated_hidden_settings(scenario))

    def test_manual_test_skips_generation_for_ready_scenario(self):
        payload = build_scenario_payload("manual_ready_case")
        payload["hidden_context"]["current_call_contactable"] = True
        scenario = Scenario.from_dict(payload)

        self.assertFalse(_manual_test_requires_generated_hidden_settings(scenario))

    def test_local_manual_hydration_fills_placeholder_seed_without_model(self):
        scenario = Scenario.from_dict(
            {
                "scenario_id": "seed_case",
                "product": {
                    "brand": "美的",
                    "category": "空气能热水器",
                    "model": "未知",
                    "purchase_channel": "未知",
                },
                "customer": {
                    "full_name": "未知",
                    "surname": "未知",
                    "phone": "未知",
                    "address": "未知",
                    "persona": "未知",
                    "speech_style": "未知",
                },
                "request": {
                    "request_type": "fault",
                    "issue": "未知",
                    "desired_resolution": "未知",
                    "availability": "未知",
                },
                "hidden_context": {},
                "required_slots": ["issue_description", "surname", "phone", "address", "request_type"],
                "max_turns": 20,
            }
        )

        hydrated = _hydrate_manual_test_scenario_locally(scenario)

        self.assertNotEqual(hydrated.customer.full_name, "未知")
        self.assertNotEqual(hydrated.customer.phone, "未知")
        self.assertNotEqual(hydrated.customer.address, "未知")
        self.assertNotEqual(hydrated.request.issue, "未知")
        self.assertTrue(hydrated.hidden_context["current_call_contactable"])
        self.assertFalse(hydrated.hidden_context["service_known_address"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
