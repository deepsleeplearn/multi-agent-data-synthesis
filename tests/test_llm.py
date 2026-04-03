from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from multi_agent_data_synthesis.config import AppConfig
from multi_agent_data_synthesis.llm import OpenAIChatClient


def build_config() -> AppConfig:
    root = Path("/tmp/multi-agent-data-synthesis-tests")
    return AppConfig(
        openai_base_url="https://aimpapi.midea.com/t-aigc/mip-chat-app/openai/standard/v1/chat/completions",
        openai_api_key="test-api-key",
        user="test-user",
        default_model="gpt-4o",
        user_agent_model="gpt-4o",
        service_agent_model="gpt-4o",
        default_temperature=0.7,
        service_ok_prefix_probability=0.7,
        second_round_include_issue_probability=0.5,
        max_rounds=20,
        max_concurrency=5,
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
        service_known_address_probability=0.2,
        service_known_address_matches_probability=0.8,
        address_collection_followup_probability=0.35,
        address_confirmation_direct_correction_probability=0.5,
    )


class RecordingChatClient(OpenAIChatClient):
    def __init__(self, responses: list[dict]):
        super().__init__(build_config())
        self.responses = responses
        self.sent_requests: list[dict] = []

    def _send_request(self, *, headers: dict[str, str], payload: dict[str, object]) -> dict:
        self.sent_requests.append({"headers": headers, "payload": payload})
        if not self.responses:
            raise AssertionError("No prepared sync response available.")
        return self.responses.pop(0)

    async def _send_request_async(self, *, headers: dict[str, str], payload: dict[str, object]) -> dict:
        self.sent_requests.append({"headers": headers, "payload": payload})
        if not self.responses:
            raise AssertionError("No prepared async response available.")
        return self.responses.pop(0)


class OpenAIChatClientTests(unittest.TestCase):
    def test_complete_builds_aimp_headers_and_payload(self):
        client = RecordingChatClient(
            [
                {
                    "choices": [
                        {
                            "message": {
                                "content": "模型输出",
                            }
                        }
                    ]
                }
            ]
        )

        result = client.complete(
            model="gpt-4o",
            messages=[{"role": "user", "content": "你好"}],
            temperature=0.4,
            max_tokens=256,
            enable_thinking=True,
        )

        self.assertEqual(result, "模型输出")
        self.assertEqual(len(client.sent_requests), 1)
        request = client.sent_requests[0]
        self.assertEqual(request["headers"]["Aimp-Biz-Id"], "gpt-4o")
        self.assertEqual(request["headers"]["AIGC-USER"], "test-user")
        self.assertEqual(request["headers"]["Authorization"], "Bearer test-api-key")
        self.assertEqual(
            request["payload"],
            {
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "你好"}],
                "temperature": 0.4,
                "max_tokens": 256,
                "enable_thinking": True,
            },
        )

    def test_complete_json_retries_after_invalid_json(self):
        client = RecordingChatClient(
            [
                {
                    "choices": [
                        {
                            "message": {
                                "content": "这不是 JSON",
                            }
                        }
                    ]
                },
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"reply":"已修正","call_complete":false}',
                            }
                        }
                    ]
                },
            ]
        )

        payload = client.complete_json(
            model="gpt-4o",
            messages=[{"role": "user", "content": "返回 JSON"}],
        )

        self.assertEqual(payload["reply"], "已修正")
        self.assertEqual(len(client.sent_requests), 2)
        retry_messages = client.sent_requests[1]["payload"]["messages"]
        self.assertEqual(retry_messages[-1]["role"], "user")
        self.assertIn("请仅返回一个 JSON 对象", retry_messages[-1]["content"])

    def test_complete_supports_list_content(self):
        client = RecordingChatClient(
            [
                {
                    "choices": [
                        {
                            "message": {
                                "content": [
                                    {"type": "text", "text": "第一段"},
                                    {"type": "text", "text": "第二段"},
                                ]
                            }
                        }
                    ]
                }
            ]
        )

        result = client.complete(
            model="gpt-4o",
            messages=[{"role": "user", "content": "你好"}],
        )

        self.assertEqual(result, "第一段第二段")

    def test_gpt_5_3_chat_omits_temperature_and_max_tokens_by_default(self):
        client = RecordingChatClient(
            [
                {
                    "choices": [
                        {
                            "message": {
                                "content": "模型输出",
                            }
                        }
                    ]
                }
            ]
        )

        client.complete(
            model="gpt-5.3-chat",
            messages=[{"role": "user", "content": "你好"}],
            temperature=0.4,
            max_tokens=256,
            enable_thinking=True,
        )

        request = client.sent_requests[0]
        self.assertEqual(
            request["payload"],
            {
                "model": "gpt-5.3-chat",
                "messages": [{"role": "user", "content": "你好"}],
                "enable_thinking": True,
            },
        )

    def test_model_request_profiles_can_override_param_names(self):
        client = RecordingChatClient(
            [
                {
                    "choices": [
                        {
                            "message": {
                                "content": "模型输出",
                            }
                        }
                    ]
                }
            ]
        )

        with patch.dict(
            os.environ,
            {
                "MODEL_REQUEST_PROFILES": (
                    '{"default":{"include_max_tokens":false},'
                    '"custom-model":{"include_temperature":false,'
                    '"include_max_tokens":true,'
                    '"max_tokens_param":"max_completion_tokens",'
                    '"include_enable_thinking":false,'
                    '"extra_body":{"reasoning_effort":"medium"}}}'
                )
            },
            clear=False,
        ):
            client.complete(
                model="custom-model",
                messages=[{"role": "user", "content": "你好"}],
                temperature=0.2,
                max_tokens=128,
                enable_thinking=True,
            )

        request = client.sent_requests[0]
        self.assertEqual(
            request["payload"],
            {
                "model": "custom-model",
                "messages": [{"role": "user", "content": "你好"}],
                "max_completion_tokens": 128,
                "reasoning_effort": "medium",
            },
        )


class OpenAIChatClientAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_complete_json_async_retries_after_invalid_json(self):
        client = RecordingChatClient(
            [
                {
                    "choices": [
                        {
                            "message": {
                                "content": "still not json",
                            }
                        }
                    ]
                },
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"reply":"异步成功","call_complete":true}',
                            }
                        }
                    ]
                },
            ]
        )

        payload = await client.complete_json_async(
            model="gpt-4o",
            messages=[{"role": "user", "content": "异步返回 JSON"}],
        )

        self.assertEqual(payload["reply"], "异步成功")
        self.assertTrue(payload["call_complete"])
        self.assertEqual(len(client.sent_requests), 2)
