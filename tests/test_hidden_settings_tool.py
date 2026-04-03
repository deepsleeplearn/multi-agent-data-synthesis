from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from multi_agent_data_synthesis.config import AppConfig
from multi_agent_data_synthesis.hidden_settings_tool import (
    HiddenSettingsRepository,
    HiddenSettingsTool,
)
from multi_agent_data_synthesis.schemas import Scenario


class SequenceFakeClient:
    def __init__(self, responses: list[dict]):
        self.responses = responses
        self.calls = 0

    def complete_json(self, **kwargs):
        if self.calls >= len(self.responses):
            raise AssertionError("Fake client ran out of prepared responses.")
        response = self.responses[self.calls]
        self.calls += 1
        return response


def build_config(
    store_path: Path,
    *,
    current_call_contactable_probability: float = 0.75,
    phone_collection_second_attempt_probability: float = 0.35,
    phone_collection_third_attempt_probability: float = 0.2,
    service_known_address_probability: float = 0.2,
    service_known_address_matches_probability: float = 0.8,
    address_collection_followup_probability: float = 0.35,
) -> AppConfig:
    return AppConfig(
        openai_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        openai_api_key="sk-a5735e44c73347978f9a4664ef8bea7d",
        default_model="qwen3.5-plus",
        user_agent_model="qwen3.5-plus",
        service_agent_model="qwen3.5-plus",
        default_temperature=0.7,
        service_ok_prefix_probability=0.7,
        max_rounds=20,
        max_concurrency=5,
        request_timeout=30,
        data_dir=store_path.parent,
        output_dir=store_path.parent,
        hidden_settings_store=store_path,
        hidden_settings_similarity_threshold=0.82,
        hidden_settings_duplicate_threshold=0.5,
        hidden_settings_max_attempts=3,
        current_call_contactable_probability=current_call_contactable_probability,
        phone_collection_second_attempt_probability=phone_collection_second_attempt_probability,
        phone_collection_third_attempt_probability=phone_collection_third_attempt_probability,
        service_known_address_probability=service_known_address_probability,
        service_known_address_matches_probability=service_known_address_matches_probability,
        address_collection_followup_probability=address_collection_followup_probability,
    )


def build_base_scenario() -> Scenario:
    return Scenario.from_dict(
        {
            "scenario_id": "midea_heat_pump_fault_test_001",
            "product": {
                "brand": "美的",
                "category": "空气能热水器",
                "model": "KF66/200L-MI(E4)",
                "purchase_channel": "京东官方旗舰店",
            },
            "customer": {
                "full_name": "占位用户",
                "surname": "占",
                "phone": "13800000000",
                "address": "占位地址",
                "persona": "占位画像",
            },
            "request": {
                "request_type": "fault",
                "issue": "占位问题",
                "desired_resolution": "占位诉求",
                "availability": "占位时间",
            },
            "required_slots": [
                "issue_description",
                "surname",
                "phone",
                "address",
                "product_model",
                "request_type",
                "availability",
            ],
            "max_turns": 20,
            "tags": ["midea", "heat_pump_water_heater"],
        }
    )


def build_installation_scenario() -> Scenario:
    return Scenario.from_dict(
        {
            "scenario_id": "midea_heat_pump_installation_test_001",
            "product": {
                "brand": "美的",
                "category": "空气能热水机",
                "model": "RSJ-20/300RDN3-C",
                "purchase_channel": "天猫官方旗舰店",
            },
            "customer": {
                "full_name": "占位用户",
                "surname": "占",
                "phone": "13800000000",
                "address": "占位地址",
                "persona": "占位画像",
            },
            "request": {
                "request_type": "installation",
                "issue": "占位安装问题",
                "desired_resolution": "占位诉求",
                "availability": "占位时间",
            },
            "required_slots": [
                "issue_description",
                "surname",
                "phone",
                "address",
                "product_model",
                "request_type",
                "availability",
            ],
            "max_turns": 20,
            "tags": ["midea", "heat_pump_water_heater", "installation"],
        }
    )


def build_candidate(
    *,
    full_name: str,
    surname: str,
    phone: str,
    address: str,
    persona: str,
    issue: str,
    desired_resolution: str,
    availability: str,
    emotion: str,
    urgency: str,
    prior_attempts: str,
    special_constraints: str,
) -> dict:
    return {
        "customer": {
            "full_name": full_name,
            "surname": surname,
            "phone": phone,
            "address": address,
            "persona": persona,
        },
        "request": {
            "request_type": "fault",
            "issue": issue,
            "desired_resolution": desired_resolution,
            "availability": availability,
        },
        "hidden_context": {
            "emotion": emotion,
            "urgency": urgency,
            "prior_attempts": prior_attempts,
            "special_constraints": special_constraints,
        },
    }


class HiddenSettingsToolTests(unittest.TestCase):
    def test_rejects_unsupported_brand(self):
        with self.assertRaises(ValueError):
            Scenario.from_dict(
                {
                    "scenario_id": "bad_brand_case",
                    "product": {
                        "brand": "海尔",
                        "category": "空气能热水器",
                        "model": "X1",
                        "purchase_channel": "门店",
                    },
                    "customer": {
                        "full_name": "张三",
                        "surname": "张",
                        "phone": "13800000000",
                        "address": "上海市浦东新区1号",
                        "persona": "普通用户",
                    },
                    "request": {
                        "request_type": "fault",
                        "issue": "测试问题",
                        "desired_resolution": "测试诉求",
                        "availability": "周末",
                    },
                    "required_slots": ["surname"],
                    "max_turns": 2,
                    "tags": [],
                }
            )

    def test_generate_hidden_settings_persists_history(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "hidden_settings_history.jsonl"
            tool = HiddenSettingsTool(
                SequenceFakeClient(
                    [
                        build_candidate(
                            full_name="李敏",
                            surname="李",
                            phone="13912345678",
                            address="江苏省苏州市吴中区金枫路88号3幢1201室",
                            persona="说话直接，比较关注老人洗澡热水是否稳定",
                            issue="家里的美的空气能热水器最近早晚水温不稳定，偶尔会突然变温",
                            desired_resolution="希望尽快安排师傅上门检查温控和主机运行情况",
                            availability="周五晚上七点后或者周日白天",
                            emotion="有些着急但还算克制",
                            urgency="中高",
                            prior_attempts="重启过一次机器，没有改善",
                            special_constraints="家里有老人，晚上更需要稳定热水",
                        )
                    ]
                ),
                build_config(store_path),
            )

            scenario = build_base_scenario()
            generated = tool.generate_for_scenario(scenario)

            self.assertEqual(generated.customer.full_name, "李敏")
            self.assertEqual(generated.customer.surname, "李")
            self.assertEqual(generated.request.request_type, "fault")
            self.assertTrue(store_path.exists())

            records = HiddenSettingsRepository(store_path).load()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].generated_customer["full_name"], "李敏")
            self.assertEqual(records[0].duplicate_rate, 0.0)

    def test_retries_when_candidate_is_too_similar(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "hidden_settings_history.jsonl"
            config = build_config(store_path)
            scenario = build_base_scenario()

            first_candidate = build_candidate(
                full_name="李敏",
                surname="李",
                phone="13912345678",
                address="江苏省苏州市吴中区金枫路88号3幢1201室",
                persona="说话直接，比较关注老人洗澡热水是否稳定",
                issue="家里的美的空气能热水器最近早晚水温不稳定，偶尔会突然变温",
                desired_resolution="希望尽快安排师傅上门检查温控和主机运行情况",
                availability="周五晚上七点后或者周日白天",
                emotion="有些着急但还算克制",
                urgency="中高",
                prior_attempts="重启过一次机器，没有改善",
                special_constraints="家里有老人，晚上更需要稳定热水",
            )
            second_candidate = build_candidate(
                full_name="周岚",
                surname="周",
                phone="13755556666",
                address="浙江省宁波市鄞州区天童南路818号2幢602室",
                persona="语速偏快，希望一次说清楚，但愿意配合客服确认信息",
                issue="空气能热水器白天还能用，晚上多人连续洗澡时热水明显不够，外机还会发出闷响",
                desired_resolution="想先确认故障原因，并尽快预约上门检测",
                availability="周六上午九点到十二点",
                emotion="焦虑但理性",
                urgency="高",
                prior_attempts="看过面板设置，也清理过外机周围杂物，问题还在",
                special_constraints="小区周末白天才能进施工人员，工作日家里没人",
            )

            seed_tool = HiddenSettingsTool(SequenceFakeClient([first_candidate]), config)
            seed_tool.generate_for_scenario(scenario)

            retry_client = SequenceFakeClient([first_candidate, second_candidate])
            retry_tool = HiddenSettingsTool(retry_client, config)
            generated = retry_tool.generate_for_scenario(scenario.clone_with_id("midea_heat_pump_fault_test_002"))

            self.assertEqual(retry_client.calls, 2)
            self.assertEqual(generated.customer.full_name, "周岚")
            self.assertEqual(generated.customer.phone, "13755556666")

            records = HiddenSettingsRepository(store_path).load()
            self.assertEqual(len(records), 2)
            self.assertEqual(records[-1].generated_customer["full_name"], "周岚")

    def test_contactable_current_call_plan_can_be_forced(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "hidden_settings_history.jsonl"
            tool = HiddenSettingsTool(
                SequenceFakeClient(
                    [
                        build_candidate(
                            full_name="李敏",
                            surname="李",
                            phone="13912345678",
                            address="江苏省苏州市吴中区金枫路88号3幢1201室",
                            persona="说话直接，比较关注老人洗澡热水是否稳定",
                            issue="家里的美的空气能热水器最近早晚水温不稳定，偶尔会突然变温",
                            desired_resolution="希望尽快安排师傅上门检查温控和主机运行情况",
                            availability="周五晚上七点后或者周日白天",
                            emotion="有些着急但还算克制",
                            urgency="中高",
                            prior_attempts="重启过一次机器，没有改善",
                            special_constraints="家里有老人，晚上更需要稳定热水",
                        )
                    ]
                ),
                build_config(store_path, current_call_contactable_probability=1.0),
            )

            generated = tool.generate_for_scenario(build_base_scenario())

            self.assertTrue(generated.hidden_context["current_call_contactable"])
            self.assertEqual(generated.hidden_context["contact_phone"], generated.customer.phone)
            self.assertEqual(generated.hidden_context["phone_input_attempts_required"], 0)
            self.assertEqual(generated.hidden_context["phone_input_round_3"], f"{generated.customer.phone}#")

    def test_backup_phone_plan_can_require_second_attempt(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "hidden_settings_history.jsonl"
            tool = HiddenSettingsTool(
                SequenceFakeClient(
                    [
                        build_candidate(
                            full_name="赵欣",
                            surname="赵",
                            phone="13876543210",
                            address="广东省佛山市顺德区大良街道南国路99号6栋2203室",
                            persona="语气温和，但希望客服快一点登记完",
                            issue="新装的空气能热水器试机时发现制热速度偏慢，想尽快预约检查",
                            desired_resolution="尽快安排人员上门确认安装情况和机器状态",
                            availability="周日下午两点后",
                            emotion="有些担心",
                            urgency="中",
                            prior_attempts="暂时还没有自行处理",
                            special_constraints="白天家里只有老人，最好周末联系",
                        )
                    ]
                ),
                build_config(
                    store_path,
                    current_call_contactable_probability=0.0,
                    phone_collection_second_attempt_probability=1.0,
                ),
            )

            generated = tool.generate_for_scenario(build_base_scenario())

            self.assertFalse(generated.hidden_context["current_call_contactable"])
            self.assertEqual(generated.hidden_context["phone_input_attempts_required"], 2)
            self.assertNotEqual(generated.hidden_context["contact_phone"], generated.customer.phone)
            self.assertTrue(str(generated.hidden_context["phone_input_round_1"]).endswith("#"))
            self.assertTrue(str(generated.hidden_context["phone_input_round_2"]).endswith("#"))
            self.assertTrue(str(generated.hidden_context["phone_input_round_3"]).endswith("#"))

    def test_backup_phone_plan_can_require_third_attempt(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "hidden_settings_history.jsonl"
            tool = HiddenSettingsTool(
                SequenceFakeClient(
                    [
                        build_candidate(
                            full_name="赵欣",
                            surname="赵",
                            phone="13876543210",
                            address="广东省佛山市顺德区大良街道南国路99号6栋2203室",
                            persona="语气温和，但希望客服快一点登记完",
                            issue="新装的空气能热水器试机时发现制热速度偏慢，想尽快预约检查",
                            desired_resolution="尽快安排人员上门确认安装情况和机器状态",
                            availability="周日下午两点后",
                            emotion="有些担心",
                            urgency="中",
                            prior_attempts="暂时还没有自行处理",
                            special_constraints="白天家里只有老人，最好周末联系",
                        )
                    ]
                ),
                build_config(
                    store_path,
                    current_call_contactable_probability=0.0,
                    phone_collection_second_attempt_probability=0.0,
                    phone_collection_third_attempt_probability=1.0,
                ),
            )

            generated = tool.generate_for_scenario(build_base_scenario())

            self.assertFalse(generated.hidden_context["current_call_contactable"])
            self.assertEqual(generated.hidden_context["phone_input_attempts_required"], 3)
            self.assertNotEqual(generated.hidden_context["phone_input_round_1"], generated.hidden_context["contact_phone"] + "#")
            self.assertNotEqual(generated.hidden_context["phone_input_round_2"], generated.hidden_context["contact_phone"] + "#")
            self.assertEqual(generated.hidden_context["phone_input_round_3"], generated.hidden_context["contact_phone"] + "#")

    def test_known_address_plan_can_be_forced(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "hidden_settings_history.jsonl"
            tool = HiddenSettingsTool(
                SequenceFakeClient(
                    [
                        build_candidate(
                            full_name="赵欣",
                            surname="赵",
                            phone="13876543210",
                            address="广东省佛山市顺德区大良街道南国路99号6栋2203室",
                            persona="语气温和，但希望客服快一点登记完",
                            issue="新装的空气能热水器试机时发现制热速度偏慢，想尽快预约检查",
                            desired_resolution="尽快安排人员上门确认安装情况和机器状态",
                            availability="周日下午两点后",
                            emotion="有些担心",
                            urgency="中",
                            prior_attempts="暂时还没有自行处理",
                            special_constraints="白天家里只有老人，最好周末联系",
                        )
                    ]
                ),
                build_config(
                    store_path,
                    service_known_address_probability=1.0,
                    service_known_address_matches_probability=1.0,
                    address_collection_followup_probability=0.0,
                ),
            )

            generated = tool.generate_for_scenario(build_base_scenario())

            self.assertTrue(generated.hidden_context["service_known_address"])
            self.assertTrue(generated.hidden_context["service_known_address_matches_actual"])
            self.assertEqual(
                generated.hidden_context["service_known_address_value"],
                generated.customer.address,
            )

    def test_address_followup_plan_can_be_forced(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "hidden_settings_history.jsonl"
            tool = HiddenSettingsTool(
                SequenceFakeClient(
                    [
                        build_candidate(
                            full_name="赵欣",
                            surname="赵",
                            phone="13876543210",
                            address="广东省佛山市顺德区大良街道南国路99号6栋2203室",
                            persona="语气温和，但希望客服快一点登记完",
                            issue="新装的空气能热水器试机时发现制热速度偏慢，想尽快预约检查",
                            desired_resolution="尽快安排人员上门确认安装情况和机器状态",
                            availability="周日下午两点后",
                            emotion="有些担心",
                            urgency="中",
                            prior_attempts="暂时还没有自行处理",
                            special_constraints="白天家里只有老人，最好周末联系",
                        )
                    ]
                ),
                build_config(
                    store_path,
                    service_known_address_probability=0.0,
                    address_collection_followup_probability=1.0,
                ),
            )

            generated = tool.generate_for_scenario(build_base_scenario())

            self.assertFalse(generated.hidden_context["service_known_address"])
            self.assertNotEqual(
                generated.hidden_context["address_input_round_1"],
                generated.customer.address,
            )
            self.assertEqual(
                generated.hidden_context["address_input_round_2"],
                generated.customer.address,
            )

    def test_stale_known_address_stays_precise(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "hidden_settings_history.jsonl"
            tool = HiddenSettingsTool(
                SequenceFakeClient(
                    [
                        build_candidate(
                            full_name="赵欣",
                            surname="赵",
                            phone="13876543210",
                            address="浙江省杭州市西湖区文三路159号阳光花园12幢3单元502室",
                            persona="语气温和，但希望客服快一点登记完",
                            issue="新装的空气能热水器试机时发现制热速度偏慢，想尽快预约检查",
                            desired_resolution="尽快安排人员上门确认安装情况和机器状态",
                            availability="周日下午两点后",
                            emotion="有些担心",
                            urgency="中",
                            prior_attempts="暂时还没有自行处理",
                            special_constraints="白天家里只有老人，最好周末联系",
                        )
                    ]
                ),
                build_config(
                    store_path,
                    service_known_address_probability=1.0,
                    service_known_address_matches_probability=0.0,
                ),
            )

            generated = tool.generate_for_scenario(build_base_scenario())
            stale_address = str(generated.hidden_context["service_known_address_value"])

            self.assertNotIn("附近", stale_address)
            self.assertIn("省", stale_address)
            self.assertIn("市", stale_address)
            self.assertIn("区", stale_address)

    def test_installation_hidden_context_infers_product_arrived(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "hidden_settings_history.jsonl"
            tool = HiddenSettingsTool(
                SequenceFakeClient(
                    [
                        {
                            "customer": {
                                "full_name": "赵欣",
                                "surname": "赵",
                                "phone": "13876543210",
                                "address": "广东省佛山市顺德区大良街道南国路99号6栋2203室",
                                "persona": "说话随意一点，希望安装尽快安排",
                            },
                            "request": {
                                "request_type": "installation",
                                "issue": "机器已经送到家了，还没拆箱，想装一下",
                                "desired_resolution": "先登记，等后面安排安装",
                                "availability": "周日下午两点后",
                            },
                            "hidden_context": {
                                "emotion": "正常",
                                "urgency": "中",
                                "prior_attempts": "还没自己处理",
                                "special_constraints": "白天家里有人",
                            },
                        }
                    ]
                ),
                build_config(store_path),
            )

            generated = tool.generate_for_scenario(build_installation_scenario())

            self.assertEqual(generated.request.request_type, "installation")
            self.assertEqual(generated.hidden_context["product_arrived"], "yes")


if __name__ == "__main__":
    unittest.main(verbosity=2)
