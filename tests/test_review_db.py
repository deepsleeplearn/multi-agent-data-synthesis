from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from review_db.fetch_reviews import fetch_manual_test_reviews, format_review_record_as_cli, format_review_records


class ReviewDbFetchTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "reviews.sqlite3"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_fetch_reviews_supports_legacy_database_without_username_column(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE manual_test_reviews (
                    session_id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    aborted_reason TEXT NOT NULL,
                    is_correct INTEGER NOT NULL,
                    failed_flow_stage TEXT NOT NULL,
                    reviewer_notes TEXT NOT NULL,
                    persist_to_db INTEGER NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT NOT NULL,
                    reviewed_at TEXT NOT NULL,
                    review_payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT INTO manual_test_reviews (
                    session_id,
                    scenario_id,
                    status,
                    aborted_reason,
                    is_correct,
                    failed_flow_stage,
                    reviewer_notes,
                    persist_to_db,
                    started_at,
                    ended_at,
                    reviewed_at,
                    review_payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "legacy-session",
                    "legacy-case",
                    "aborted",
                    "user_exit",
                    0,
                    "address_collection",
                    "legacy notes",
                    1,
                    "2026-01-01T00:00:00+00:00",
                    "2026-01-01T00:01:00+00:00",
                    "2026-01-01T00:02:00+00:00",
                    json.dumps(
                        {
                            "session_id": "legacy-session",
                            "review": {"notes": "legacy notes"},
                            "transcript": [],
                            "trace": [],
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
            conn.commit()

        records = fetch_manual_test_reviews(self.db_path)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["session_id"], "legacy-session")
        self.assertEqual(records[0]["username"], "")
        self.assertEqual(records[0]["scenario_id"], "legacy-case")

    def test_fetch_reviews_returns_username_and_transcript_from_newer_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE manual_test_reviews (
                    session_id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    username TEXT,
                    status TEXT NOT NULL,
                    aborted_reason TEXT NOT NULL,
                    is_correct INTEGER NOT NULL,
                    failed_flow_stage TEXT NOT NULL,
                    reviewer_notes TEXT NOT NULL,
                    persist_to_db INTEGER NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT NOT NULL,
                    reviewed_at TEXT NOT NULL,
                    review_payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT INTO manual_test_reviews (
                    session_id,
                    scenario_id,
                    username,
                    status,
                    aborted_reason,
                    is_correct,
                    failed_flow_stage,
                    reviewer_notes,
                    persist_to_db,
                    started_at,
                    ended_at,
                    reviewed_at,
                    review_payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "new-session",
                    "new-case",
                    "tester",
                    "completed",
                    "",
                    1,
                    "",
                    "",
                    1,
                    "2026-02-01T00:00:00+00:00",
                    "2026-02-01T00:01:00+00:00",
                    "2026-02-01T00:02:00+00:00",
                    json.dumps(
                        {
                            "session_id": "new-session",
                            "username": "tester",
                            "transcript": [
                                {
                                    "speaker": "客服",
                                    "text": "好的",
                                    "previous_user_intent_model_inference_used": False,
                                }
                            ],
                            "trace": [{"previous_user_intent_model_inference_used": False}],
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
            conn.commit()

        records = fetch_manual_test_reviews(self.db_path, session_id="new-session")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["username"], "tester")
        self.assertEqual(records[0]["transcript"][0]["speaker"], "客服")
        self.assertFalse(records[0]["trace"][0]["previous_user_intent_model_inference_used"])

    def test_format_review_record_as_cli_restores_terminal_style_output(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE manual_test_reviews (
                    session_id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    username TEXT,
                    status TEXT NOT NULL,
                    aborted_reason TEXT NOT NULL,
                    is_correct INTEGER NOT NULL,
                    failed_flow_stage TEXT NOT NULL,
                    reviewer_notes TEXT NOT NULL,
                    persist_to_db INTEGER NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT NOT NULL,
                    reviewed_at TEXT NOT NULL,
                    review_payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT INTO manual_test_reviews (
                    session_id,
                    scenario_id,
                    username,
                    status,
                    aborted_reason,
                    is_correct,
                    failed_flow_stage,
                    reviewer_notes,
                    persist_to_db,
                    started_at,
                    ended_at,
                    reviewed_at,
                    review_payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "cli-session",
                    "cli-case",
                    "tester",
                    "aborted",
                    "user_exit",
                    0,
                    "address_collection",
                    "地址确认有误",
                    1,
                    "2026-03-01T00:00:00+00:00",
                    "2026-03-01T00:01:00+00:00",
                    "2026-03-01T00:02:00+00:00",
                    json.dumps(
                        {
                            "session_id": "cli-session",
                            "scenario_id": "cli-case",
                            "rounds_limit": 6,
                            "session_config": {
                                "known_address": "浙江省杭州市余杭区玉鸟路1号",
                            },
                            "scenario": {
                                "scenario_id": "cli-case",
                                "product": {
                                    "brand": "美的",
                                    "category": "空气能热水机",
                                    "model": "KF66",
                                },
                                "request": {
                                    "request_type": "fault",
                                },
                            },
                            "review": {
                                "is_correct": False,
                                "failed_flow_stage": "address_collection",
                                "notes": "地址确认有误",
                            },
                            "transcript": [
                                {
                                    "speaker": "用户",
                                    "text": "热水器坏了",
                                    "round_index": 1,
                                    "round_label": "1",
                                },
                                {
                                    "speaker": "客服",
                                    "text": "请问您家的详细地址是？",
                                    "round_index": 1,
                                    "round_label": "1*",
                                    "previous_user_intent_model_inference_used": True,
                                },
                            ],
                            "trace": [],
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
            conn.commit()

        records = fetch_manual_test_reviews(self.db_path, session_id="cli-session")

        cli_output = format_review_record_as_cli(records[0])
        self.assertIn("Session ID: cli-session", cli_output)
        self.assertIn("场景: cli-case", cli_output)
        self.assertIn("已知地址: 浙江省杭州市余杭区玉鸟路1号", cli_output)
        self.assertIn("[1] 用户: 热水器坏了", cli_output)
        self.assertIn("[1*] 客服: 请问您家的详细地址是？", cli_output)
        self.assertIn("评审结果: 错误", cli_output)
        self.assertIn("出错流程: address_collection", cli_output)

    def test_format_review_records_keeps_json_default_and_supports_cli_mode(self):
        record = {
            "session_id": "session-1",
            "scenario_id": "case-1",
            "username": "tester",
            "status": "completed",
            "aborted_reason": "",
            "review_payload": {
                "scenario": {
                    "product": {"brand": "美的", "category": "空气能热水机", "model": "KF66"},
                    "request": {"request_type": "fault"},
                },
                "transcript": [],
            },
            "transcript": [],
        }

        json_output = format_review_records([record])
        cli_output = format_review_records([record], output_format="cli")

        self.assertIn('"session_id": "session-1"', json_output)
        self.assertIn("Session ID: session-1", cli_output)
        self.assertIn("[无对话内容]", cli_output)


if __name__ == "__main__":
    unittest.main()
