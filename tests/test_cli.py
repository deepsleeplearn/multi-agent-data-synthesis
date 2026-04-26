from __future__ import annotations

import argparse
import asyncio
import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from css_data_synthesis_test.cli import (
    MANUAL_CONTACT_PHONE_PREFIXES,
    _configure_manual_test_known_address,
    _hydrate_manual_test_scenario_locally,
    _mock_manual_contact_phone,
    _manual_test_requires_generated_hidden_settings,
    _resolve_interactive_max_rounds,
    _utterance_reference_summary_line,
    _validate_output_flags,
    build_parser,
    run_generate_async,
    run_interactive_test,
)
from css_data_synthesis_test.orchestrator import DialogueOrchestrator
from tests.test_orchestrator import build_scenario
from tests.test_manual_test import build_scenario_payload
from css_data_synthesis_test.schemas import Scenario


class CliTests(unittest.TestCase):
    def test_generate_parser_defaults_write_output_to_false(self):
        parser = build_parser()

        args = parser.parse_args(["generate", "--count", "1"])

        self.assertFalse(args.write_output)

    def test_generate_parser_accepts_write_output_flag(self):
        parser = build_parser()

        args = parser.parse_args(["generate", "--count", "1", "--write-output"])

        self.assertTrue(args.write_output)

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

    def test_interactive_parser_accepts_show_address_state_flag(self):
        parser = build_parser()

        args = parser.parse_args(["interactive-test", "--show-address-state"])

        self.assertTrue(args.show_address_state)

    def test_interactive_parser_defaults_address_state_to_hidden(self):
        parser = build_parser()

        args = parser.parse_args(["interactive-test"])

        self.assertFalse(args.show_address_state)
        self.assertFalse(args.hide_address_state)

    def test_interactive_parser_accepts_hide_address_state_flag(self):
        parser = build_parser()

        args = parser.parse_args(["interactive-test", "--hide-address-state"])

        self.assertTrue(args.hide_address_state)

    def test_interactive_parser_accepts_show_final_slots_flag(self):
        parser = build_parser()

        args = parser.parse_args(["interactive-test", "--show-final-slots"])

        self.assertTrue(args.show_final_slots)

    def test_resolve_interactive_max_rounds_prefers_cli_arg(self):
        self.assertEqual(
            _resolve_interactive_max_rounds(
                args_max_rounds=40,
                scenario_max_turns=20,
                config_max_rounds=32,
            ),
            40,
        )

    def test_resolve_interactive_max_rounds_falls_back_to_scenario(self):
        self.assertEqual(
            _resolve_interactive_max_rounds(
                args_max_rounds=None,
                scenario_max_turns=20,
                config_max_rounds=32,
            ),
            20,
        )

    def test_resolve_interactive_max_rounds_uses_config_when_scenario_missing(self):
        self.assertEqual(
            _resolve_interactive_max_rounds(
                args_max_rounds=None,
                scenario_max_turns=0,
                config_max_rounds=32,
            ),
            32,
        )

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

    def test_validate_output_flags_rejects_generate_output_without_write_output(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "generate",
                "--count",
                "1",
                "--json-output",
                "custom.json",
            ]
        )

        with self.assertRaises(SystemExit):
            _validate_output_flags(parser, args)

    def test_run_generate_async_skips_export_when_write_output_disabled(self):
        args = argparse.Namespace(
            scenario_file=SimpleNamespace(),
            count=1,
            jsonl_output=SimpleNamespace(),
            json_output=SimpleNamespace(),
            auto_hidden_settings=False,
            show_dialogue=False,
            show_persona=False,
            concurrency=None,
            write_output=False,
            persist_to_db=False,
        )
        config = SimpleNamespace(
            installation_request_probability=0.5,
            max_concurrency=2,
        )
        factory_instance = Mock()
        factory_instance.load_from_file.return_value = ["scenario"]
        factory_instance.expand_to_count.return_value = ["scenario"]
        orchestrator_instance = Mock()
        orchestrator_instance.generate_dialogues_async = AsyncMock(
            return_value=[SimpleNamespace(status="completed")]
        )

        with patch("css_data_synthesis_test.cli._load_cli_config", return_value=config):
            with patch("css_data_synthesis_test.cli.ScenarioFactory", return_value=factory_instance):
                with patch(
                    "css_data_synthesis_test.cli.DialogueOrchestrator",
                    return_value=orchestrator_instance,
                ):
                    with patch("css_data_synthesis_test.cli.write_jsonl") as write_jsonl_mock:
                        with patch("css_data_synthesis_test.cli.write_json") as write_json_mock:
                            asyncio.run(run_generate_async(args))

        write_jsonl_mock.assert_not_called()
        write_json_mock.assert_not_called()

    def test_utterance_reference_summary_line_formats_library_source(self):
        line = _utterance_reference_summary_line(
            {
                "scenario_id": "fault_case_001",
                "hidden_context": {
                    "utterance_reference_source": "library",
                    "utterance_reference_intent": "报修",
                    "utterance_reference_category": "不制热 / 无热水",
                    "utterance_reference_summary": "空气能热水器不出热水",
                    "utterance_reference_original": "现在一点热水都没有了。",
                },
            }
        )

        self.assertIn("fault_case_001", line)
        self.assertIn("参考话术库", line)
        self.assertIn("不制热 / 无热水", line)
        self.assertIn("现在一点热水都没有了。", line)

    def test_run_generate_async_prints_utterance_reference_summary_when_auto_hidden_enabled(self):
        args = argparse.Namespace(
            scenario_file=SimpleNamespace(),
            count=1,
            jsonl_output=SimpleNamespace(),
            json_output=SimpleNamespace(),
            auto_hidden_settings=True,
            show_dialogue=False,
            show_persona=False,
            concurrency=None,
            write_output=False,
            persist_to_db=False,
        )
        config = SimpleNamespace(
            installation_request_probability=0.5,
            max_concurrency=2,
        )
        factory_instance = Mock()
        factory_instance.load_from_file.return_value = ["scenario"]
        factory_instance.expand_to_count.return_value = ["scenario"]
        orchestrator_instance = Mock()
        orchestrator_instance.generate_dialogues_async = AsyncMock(
            return_value=[
                SimpleNamespace(
                    status="completed",
                    scenario={
                        "scenario_id": "fault_case_001",
                        "hidden_context": {
                            "utterance_reference_source": "library",
                            "utterance_reference_intent": "报修",
                            "utterance_reference_category": "不制热 / 无热水",
                            "utterance_reference_summary": "空气能热水器不出热水",
                            "utterance_reference_original": "现在一点热水都没有了。",
                        },
                    },
                )
            ]
        )
        buffer = io.StringIO()

        with patch("css_data_synthesis_test.cli._load_cli_config", return_value=config):
            with patch("css_data_synthesis_test.cli.ScenarioFactory", return_value=factory_instance):
                with patch(
                    "css_data_synthesis_test.cli.DialogueOrchestrator",
                    return_value=orchestrator_instance,
                ):
                    with patch("css_data_synthesis_test.cli.write_jsonl"):
                        with patch("css_data_synthesis_test.cli.write_json"):
                            with redirect_stdout(buffer):
                                asyncio.run(run_generate_async(args))

        output = buffer.getvalue()
        self.assertIn("话术参考使用情况:", output)
        self.assertIn("fault_case_001", output)
        self.assertIn("不制热 / 无热水", output)

    def test_run_interactive_test_uses_utterance_reference_when_auto_hidden_enabled(self):
        args = argparse.Namespace(
            scenario_file=SimpleNamespace(),
            scenario_id="seed_case",
            scenario_index=0,
            auto_hidden_settings=True,
            known_address="",
            write_output=False,
            output=None,
            max_rounds=None,
            show_address_state=False,
            hide_address_state=False,
            show_final_slots=False,
        )
        config = SimpleNamespace(
            service_agent_model="gpt-4o",
            default_temperature=0.0,
            service_ok_prefix_probability=0.0,
            service_query_prefix_weights={"": 1.0},
            product_routing_enabled=False,
            product_routing_apply_probability=0.0,
            product_routing_entry_weights={},
            product_routing_brand_series_weights={},
            product_routing_usage_scene_weights={},
            product_routing_purchase_or_property_weights={},
            product_routing_property_year_weights={},
            product_routing_history_confirmation_weights={},
            max_rounds=6,
        )
        scenario = build_scenario()
        generated_scenario = build_scenario()

        with patch("css_data_synthesis_test.cli._load_cli_config", return_value=config):
            with patch("css_data_synthesis_test.cli.load_manual_test_scenario", return_value=scenario):
                with patch("css_data_synthesis_test.cli.HiddenSettingsTool") as tool_cls:
                    tool_cls.return_value.generate_for_scenario.return_value = generated_scenario
                    with patch("css_data_synthesis_test.cli.OpenAIChatClient"):
                        with patch("css_data_synthesis_test.cli.ServiceAgent") as service_agent_cls:
                            service_agent_cls.return_value.policy = object()
                            with patch(
                                "css_data_synthesis_test.cli._configure_manual_test_known_address",
                                return_value=generated_scenario,
                            ):
                                with patch("css_data_synthesis_test.cli.run_manual_test_session") as run_session:
                                    run_interactive_test(args)

        tool_cls.return_value.generate_for_scenario.assert_called_once_with(
            scenario,
            use_utterance_reference=True,
        )
        run_session.assert_called_once()

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

        self.assertEqual(hydrated.customer.full_name, "未知")
        self.assertEqual(hydrated.customer.phone, "未知")
        self.assertEqual(hydrated.customer.address, "未知")
        self.assertEqual(hydrated.request.issue, "未知")
        self.assertTrue(hydrated.hidden_context["current_call_contactable"])
        self.assertEqual(hydrated.hidden_context["contact_phone_owner"], "本人当前来电")
        phone = str(hydrated.hidden_context["contact_phone"])
        self.assertEqual(len(phone), 11)
        self.assertIn(phone[:3], MANUAL_CONTACT_PHONE_PREFIXES)
        self.assertFalse(hydrated.hidden_context["service_known_address"])
        self.assertEqual(hydrated.hidden_context["address_input_rounds"], [])

    def test_mock_manual_contact_phone_uses_stable_but_generalized_prefixes(self):
        phone_a = _mock_manual_contact_phone("manual_case_a")
        phone_b = _mock_manual_contact_phone("manual_case_b")

        self.assertEqual(phone_a, _mock_manual_contact_phone("manual_case_a"))
        self.assertEqual(len(phone_a), 11)
        self.assertEqual(len(phone_b), 11)
        self.assertIn(phone_a[:3], MANUAL_CONTACT_PHONE_PREFIXES)
        self.assertIn(phone_b[:3], MANUAL_CONTACT_PHONE_PREFIXES)
        self.assertNotEqual(phone_a, phone_b)

    def test_configure_manual_test_known_address_enables_direct_confirmation(self):
        scenario = Scenario.from_dict(build_scenario_payload("manual_known_address_case"))
        printed: list[str] = []

        configured = _configure_manual_test_known_address(
            scenario,
            input_func=lambda _: " 上海市青浦区徐泾镇西郊一区1785弄40号楼301室 ",
            print_func=printed.append,
        )

        self.assertEqual(configured.customer.address, "上海市青浦区徐泾镇西郊一区1785弄40号楼301室")
        self.assertTrue(configured.hidden_context["service_known_address"])
        self.assertTrue(configured.hidden_context["service_known_address_matches_actual"])
        self.assertEqual(
            configured.hidden_context["service_known_address_value"],
            "上海市青浦区徐泾镇西郊一区1785弄40号楼301室",
        )
        self.assertIn("已设置已知地址", printed[0])

    def test_configure_manual_test_known_address_blank_keeps_inquiry_flow(self):
        scenario = Scenario.from_dict(build_scenario_payload("manual_unknown_address_case"))
        printed: list[str] = []

        configured = _configure_manual_test_known_address(
            scenario,
            input_func=lambda _: "   ",
            print_func=printed.append,
        )

        self.assertEqual(configured.customer.address, scenario.customer.address)
        self.assertFalse(configured.hidden_context["service_known_address"])
        self.assertEqual(configured.hidden_context["service_known_address_value"], "")
        self.assertFalse(configured.hidden_context["service_known_address_matches_actual"])
        self.assertIn("未设置已知地址", printed[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
