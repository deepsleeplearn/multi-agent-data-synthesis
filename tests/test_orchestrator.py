from __future__ import annotations

import unittest
from pathlib import Path

from multi_agent_data_synthesis.config import AppConfig
from multi_agent_data_synthesis.orchestrator import DialogueOrchestrator
from multi_agent_data_synthesis.schemas import (
    SERVICE_SPEAKER,
    USER_SPEAKER,
    Scenario,
)


def build_config() -> AppConfig:
    root = Path("/tmp/multi-agent-data-synthesis-tests")
    return AppConfig(
        openai_base_url="https://example.com/v1/chat/completions",
        openai_api_key="test-api-key",
        user="test-user",
        default_model="gpt-4o",
        user_agent_model="gpt-4o",
        service_agent_model="gpt-4o",
        default_temperature=0.7,
        service_ok_prefix_probability=0.0,
        second_round_include_issue_probability=0.5,
        max_rounds=4,
        max_concurrency=2,
        request_timeout=30,
        data_dir=root,
        output_dir=root,
        hidden_settings_store=root / "hidden_settings_history.jsonl",
        hidden_settings_similarity_threshold=0.82,
        hidden_settings_duplicate_threshold=0.5,
        hidden_settings_max_attempts=3,
        hidden_settings_multi_fault_probability=0.1,
        installation_request_probability=0.5,
        current_call_contactable_probability=0.75,
        phone_collection_second_attempt_probability=0.35,
        phone_collection_third_attempt_probability=0.2,
        phone_collection_invalid_short_probability=0.34,
        phone_collection_invalid_long_probability=0.33,
        phone_collection_invalid_pattern_probability=0.33,
        phone_collection_invalid_digit_mismatch_probability=0.33,
        service_known_address_probability=0.2,
        service_known_address_matches_probability=0.8,
        address_collection_followup_probability=0.35,
        address_segmented_reply_probability=0.35,
        address_segment_rounds_weights={"2": 0.45, "3": 0.35, "4": 0.20},
        address_segment_strategy_weights={
            "province_city__district__locality__detail": 0.20,
            "province_city_district__locality__detail": 0.30,
            "province_city__district_locality__detail": 0.15,
            "province_city__district__locality_detail": 0.10,
            "province_city_district_locality__detail": 0.15,
            "province_city_district__locality_detail": 0.10,
        },
        address_input_omit_province_city_suffix_probability=0.0,
        address_confirmation_direct_correction_probability=0.5,
    )


def build_scenario() -> Scenario:
    return Scenario.from_dict(
        {
            "scenario_id": "fault_case_001",
            "product": {
                "brand": "美的",
                "category": "空气能热水器",
                "model": "KF-01",
                "purchase_channel": "京东",
            },
            "customer": {
                "full_name": "张三",
                "surname": "张",
                "phone": "13800000001",
                "address": "上海市浦东新区测试路1号",
                "persona": "普通用户",
                "speech_style": "简洁",
            },
            "request": {
                "request_type": "fault",
                "issue": "启动后显示E4，热水不出来",
                "desired_resolution": "尽快安排维修",
                "availability": "明天下午",
            },
            "required_slots": ["issue_description", "request_type"],
            "max_turns": 2,
        }
    )


class StubUserAgent:
    async def respond_async(self, *, scenario: Scenario, transcript: list, round_index: int) -> dict:
        if round_index == 1:
            return {
                "reply": "对，是的，我家空气能热水器启动后显示E4故障码，热水不出来。",
                "call_complete": False,
            }
        return {"reply": "好的。", "call_complete": True}


class DialogueOrchestratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_dialogue_starts_with_user_and_exports_chinese_labels(self):
        orchestrator = DialogueOrchestrator(build_config())
        orchestrator.user_agent = StubUserAgent()
        sample = await orchestrator.generate_dialogue_async(build_scenario())

        self.assertGreaterEqual(len(sample.transcript), 3)
        self.assertEqual(sample.transcript[0].speaker, USER_SPEAKER)
        self.assertEqual(sample.transcript[0].text, "美的空气能热水器需要维修")
        self.assertEqual(sample.transcript[1].speaker, SERVICE_SPEAKER)
        self.assertEqual(sample.transcript[1].text, "您好，很高兴为您服务，请问是美的空气能热水器需要维修吗？")

        exported = sample.to_dict()
        self.assertEqual(exported["transcript"][0]["speaker"], "用户")
        self.assertEqual(exported["transcript"][1]["speaker"], "客服")
        self.assertEqual(exported["transcript"][0]["text"], "美的空气能热水器需要维修")
        self.assertIn("客服:", exported["dialogue_text"])
        self.assertIn("用户:", exported["dialogue_text"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
