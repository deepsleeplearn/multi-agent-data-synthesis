from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from multi_agent_data_synthesis.config import load_config


class ConfigTests(unittest.TestCase):
    def test_load_config_prefers_explicit_env_values(self):
        with patch.dict(
            os.environ,
            {
                "OPENAI_MODEL": "gpt-4o",
                "OPENAI_BASE_URL": "https://example.com/v1/chat/completions",
                "OPENAI_API_KEY": "env-api-key",
                "OPENAI_USER": "env-user",
                "USER_AGENT_MODEL": "user-model",
                "SERVICE_AGENT_MODEL": "service-model",
                "MAX_CONCURRENCY": "3",
            },
            clear=False,
        ):
            config = load_config()

        self.assertEqual(config.openai_base_url, "https://example.com/v1/chat/completions")
        self.assertEqual(config.openai_api_key, "env-api-key")
        self.assertEqual(config.user, "env-user")
        self.assertEqual(config.user_agent_model, "user-model")
        self.assertEqual(config.service_agent_model, "service-model")
        self.assertEqual(config.max_concurrency, 3)

    def test_load_config_allows_custom_model_when_env_is_complete(self):
        with patch.dict(
            os.environ,
            {
                "OPENAI_MODEL": "custom-model",
                "OPENAI_BASE_URL": "https://example.com/custom",
                "OPENAI_API_KEY": "custom-key",
                "OPENAI_USER": "custom-user",
            },
            clear=False,
        ):
            config = load_config()

        self.assertEqual(config.default_model, "custom-model")
        self.assertEqual(config.openai_base_url, "https://example.com/custom")
        self.assertEqual(config.openai_api_key, "custom-key")
        self.assertEqual(config.user, "custom-user")


if __name__ == "__main__":
    unittest.main(verbosity=2)
