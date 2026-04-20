from __future__ import annotations

import re
import unittest
from pathlib import Path

from css_data_synthesis_test.product_routing import (
    ROUTING_RESULT_BUILDING,
    ROUTING_RESULT_HOME,
    ROUTING_RESULT_HUMAN,
    next_product_routing_steps_from_observed_trace,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PATHS_MD = PROJECT_ROOT / "adds" / "product_routing_paths_165.md"
PATH_LINE_PATTERN = re.compile(r"^- `(?P<path_id>P\d{3})`: (?P<path>.+)$")

SEGMENT_TO_ANSWER_KEY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^品牌=COLMO$"), "brand_series.colmo"),
    (re.compile(r"^品牌=(酷风|小天鹅)$"), "brand_series.cooling_or_little_swan"),
    (re.compile(r"^系列=(真暖|真省|雪焰|暖家|煤改电|真享)$"), "brand_series.home_series"),
    (re.compile(r"^系列=烈焰$"), "brand_series.lieyan"),
    (re.compile(r"^(不知道|美的)$"), "entry.unknown"),
    (re.compile(r"^提供型号$"), "entry.model"),
    (re.compile(r"^查得家用$"), "model_lookup.home"),
    (re.compile(r"^不可判断$"), "model_lookup.unknown"),
    (re.compile(r"^查得楼宇$"), "model_lookup.building"),
    (re.compile(r"^采暖$"), "purpose.heating"),
    (re.compile(r"^用途不清楚$"), "purpose.unknown"),
    (re.compile(r"^(洗澡|生活用水)$"), "purpose.water"),
    (re.compile(r"^两个用途都有$"), "purpose.both"),
    (re.compile(r"^(是家庭|是别墅|是公寓|是理发店|肯定\(无具体\))$"), "scene.yes"),
    (re.compile(r"^场所否定$"), "scene.no"),
    (re.compile(r"^场所不清楚$"), "scene.unknown"),
    (re.compile(r"^自己购买$"), "purchase.self_buy"),
    (re.compile(r"^配套不知道$"), "purchase.unknown"),
    (re.compile(r"^楼盘配套$"), "purchase.property_bundle"),
    (re.compile(r"^21年之前$"), "property_year.before_2021"),
    (re.compile(r"^21年之后$"), "property_year.after_2021"),
    (re.compile(r"^时间不清楚$"), "property_year.unknown"),
    (re.compile(r"^(≥750升|≥72立方米/3匹)$"), "capacity.above_threshold"),
    (re.compile(r"^(<750升|<72立方米/3匹)$"), "capacity.below_threshold"),
    (re.compile(r"^容量不清楚$"), "capacity.unknown"),
]

RESULT_MAPPING = {
    "家用+可直接确认机型": ROUTING_RESULT_HOME,
    "楼宇+可直接确认机型": ROUTING_RESULT_BUILDING,
    "转人工": ROUTING_RESULT_HUMAN,
}

ANSWER_KEY_TO_PROMPT_KEY = {
    "entry.unknown": "brand_or_series",
    "entry.model": "brand_or_series",
    "brand_series.colmo": "brand_or_series",
    "brand_series.cooling_or_little_swan": "brand_or_series",
    "brand_series.home_series": "brand_or_series",
    "brand_series.lieyan": "brand_or_series",
    "purpose.heating": "usage_purpose",
    "purpose.unknown": "usage_purpose",
    "purpose.water": "usage_purpose",
    "purpose.both": "usage_purpose",
    "scene.yes": "usage_scene",
    "scene.no": "usage_scene",
    "scene.unknown": "usage_scene",
    "capacity.above_threshold": "capacity_or_hp",
    "capacity.below_threshold": "capacity_or_hp",
    "capacity.unknown": "capacity_or_hp",
    "purchase.self_buy": "purchase_or_property",
    "purchase.unknown": "purchase_or_property",
    "purchase.property_bundle": "purchase_or_property",
    "property_year.before_2021": "property_year",
    "property_year.after_2021": "property_year",
    "property_year.unknown": "property_year",
}


def _normalize_result_label(label: str) -> str:
    return re.sub(r"\s+", "", str(label or "").strip())


def _segment_to_answer_key(segment: str) -> str:
    normalized = str(segment or "").strip()
    for pattern, answer_key in SEGMENT_TO_ANSWER_KEY_PATTERNS:
        if pattern.fullmatch(normalized):
            return answer_key
    raise AssertionError(f"未覆盖的路径片段: {normalized}")


def _parse_paths_from_markdown() -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []
    for raw_line in PATHS_MD.read_text(encoding="utf-8").splitlines():
        matched = PATH_LINE_PATTERN.match(raw_line.strip())
        if not matched:
            continue
        path_id = matched.group("path_id")
        raw_path = matched.group("path")
        segments = [segment.strip() for segment in raw_path.split("->")]
        if len(segments) < 2:
            raise AssertionError(f"{path_id} 路径定义无效: {raw_path}")
        if segments[0] != "询问型号":
            raise AssertionError(f"{path_id} 起始片段不是“询问型号”: {raw_path}")
        result_label = _normalize_result_label(segments[-1])
        expected_result = RESULT_MAPPING.get(result_label)
        if expected_result is None:
            raise AssertionError(f"{path_id} 终点状态未覆盖: {segments[-1]}")
        trace = [_segment_to_answer_key(segment) for segment in segments[1:-1]]
        cases.append(
            {
                "path_id": path_id,
                "raw_path": raw_path,
                "trace": trace,
                "expected_result": expected_result,
            }
        )
    return cases


class ProductRoutingPaths165Tests(unittest.TestCase):
    def test_markdown_contains_all_165_declared_paths(self):
        cases = _parse_paths_from_markdown()

        self.assertEqual(len(cases), 165)

    def test_all_165_paths_resolve_to_expected_terminal_result(self):
        for case in _parse_paths_from_markdown():
            trace = list(case["trace"])
            expected_result = str(case["expected_result"])

            with self.subTest(path_id=case["path_id"], raw_path=case["raw_path"]):
                next_steps, result = next_product_routing_steps_from_observed_trace(trace)
                self.assertEqual(result, expected_result)
                self.assertEqual(next_steps, [])

    def test_all_165_paths_follow_expected_prompt_progression(self):
        for case in _parse_paths_from_markdown():
            trace = list(case["trace"])
            if len(trace) < 2:
                continue

            with self.subTest(path_id=case["path_id"], raw_path=case["raw_path"]):
                for index in range(1, len(trace)):
                    next_answer_key = trace[index]
                    if next_answer_key.startswith("model_lookup."):
                        continue
                    prefix = trace[:index]
                    if prefix[-1] == "capacity.unknown":
                        # markdown 这里把“回到②流程”压缩成最终分支结果，没有显式展开中间的 scene 追问
                        continue
                    next_steps, result = next_product_routing_steps_from_observed_trace(prefix)
                    expected_prompt_key = ANSWER_KEY_TO_PROMPT_KEY[next_answer_key]
                    self.assertEqual(result, "", msg=f"prefix={prefix}")
                    self.assertGreaterEqual(len(next_steps), 1, msg=f"prefix={prefix}")
                    self.assertEqual(next_steps[0]["prompt_key"], expected_prompt_key, msg=f"prefix={prefix}")
