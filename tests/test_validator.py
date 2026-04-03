from __future__ import annotations

import unittest

from multi_agent_data_synthesis.schemas import DialogueSample, DialogueTurn
from multi_agent_data_synthesis.validator import validate_dialogue


class ValidatorTests(unittest.TestCase):
    def test_accepts_user_first_dialogue(self):
        sample = DialogueSample(
            scenario_id="case_000",
            status="completed",
            rounds_used=2,
            transcript=[
                DialogueTurn(speaker="user", text="美的空气能热水器需要维修", round_index=1),
                DialogueTurn(speaker="service", text="好的，请问空气能热水器现在是出现了什么问题？", round_index=1),
            ],
            collected_slots={},
            missing_slots=[],
            scenario={},
            validation={},
        )

        validation = validate_dialogue(sample)

        self.assertTrue(validation["passed"])

    def test_accepts_service_first_dialogue(self):
        sample = DialogueSample(
            scenario_id="case_001",
            status="completed",
            rounds_used=2,
            transcript=[
                DialogueTurn(speaker="service", text="您好，很高兴为您服务，请问是美的空气能热水器需要维修吗？", round_index=1),
                DialogueTurn(speaker="user", text="对，热水器加热很慢。", round_index=1),
                DialogueTurn(speaker="service", text="好的，请问您贵姓", round_index=2),
                DialogueTurn(speaker="user", text="我姓张。", round_index=2),
            ],
            collected_slots={"surname": "张"},
            missing_slots=[],
            scenario={},
            validation={},
        )

        validation = validate_dialogue(sample)

        self.assertTrue(validation["passed"])

    def test_accepts_chinese_speaker_labels(self):
        sample = DialogueSample(
            scenario_id="case_002",
            status="completed",
            rounds_used=2,
            transcript=[
                DialogueTurn(speaker="客服", text="您好，很高兴为您服务。", round_index=1),
                DialogueTurn(speaker="用户", text="对，需要报修。", round_index=1),
            ],
            collected_slots={},
            missing_slots=[],
            scenario={},
            validation={},
        )

        validation = validate_dialogue(sample)

        self.assertTrue(validation["passed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
