from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

if load_dotenv:
    load_dotenv(ENV_PATH, override=False)


@dataclass(frozen=True)
class AppConfig:
    openai_base_url: str
    openai_api_key: str
    default_model: str
    user_agent_model: str
    service_agent_model: str
    default_temperature: float
    service_ok_prefix_probability: float
    max_rounds: int
    max_concurrency: int
    request_timeout: float
    data_dir: Path
    output_dir: Path
    hidden_settings_store: Path
    hidden_settings_similarity_threshold: float
    hidden_settings_duplicate_threshold: float
    hidden_settings_max_attempts: int
    current_call_contactable_probability: float
    phone_collection_second_attempt_probability: float
    phone_collection_third_attempt_probability: float
    service_known_address_probability: float
    service_known_address_matches_probability: float
    address_collection_followup_probability: float


def load_config() -> AppConfig:
    api_key = os.getenv("OPENAI_API_KEY", "sk-a5735e44c73347978f9a4664ef8bea7d").strip()
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY. Set it in environment variables or .env.")

    default_model = os.getenv("OPENAI_MODEL", "qwen3.5-plus").strip()
    return AppConfig(
        openai_base_url=os.getenv(
            "OPENAI_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ).strip(),
        openai_api_key=api_key,
        default_model=default_model,
        user_agent_model=os.getenv("USER_AGENT_MODEL", default_model).strip(),
        service_agent_model=os.getenv("SERVICE_AGENT_MODEL", default_model).strip(),
        default_temperature=float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
        service_ok_prefix_probability=float(os.getenv("SERVICE_OK_PREFIX_PROBABILITY", "0.7")),
        max_rounds=int(os.getenv("MAX_ROUNDS", "20")),
        max_concurrency=max(1, int(os.getenv("MAX_CONCURRENCY", "5"))),
        request_timeout=float(os.getenv("REQUEST_TIMEOUT", "90")),
        data_dir=ROOT_DIR / "data",
        output_dir=ROOT_DIR / "outputs",
        hidden_settings_store=ROOT_DIR / "data" / "hidden_settings_history.jsonl",
        hidden_settings_similarity_threshold=float(
            os.getenv("HIDDEN_SETTINGS_SIMILARITY_THRESHOLD", "0.82")
        ),
        hidden_settings_duplicate_threshold=float(
            os.getenv("HIDDEN_SETTINGS_DUPLICATE_THRESHOLD", "0.5")
        ),
        hidden_settings_max_attempts=int(os.getenv("HIDDEN_SETTINGS_MAX_ATTEMPTS", "6")),
        current_call_contactable_probability=float(
            os.getenv("CURRENT_CALL_CONTACTABLE_PROBABILITY", "0.75")
        ),
        phone_collection_second_attempt_probability=float(
            os.getenv("PHONE_COLLECTION_SECOND_ATTEMPT_PROBABILITY", "0.35")
        ),
        phone_collection_third_attempt_probability=float(
            os.getenv("PHONE_COLLECTION_THIRD_ATTEMPT_PROBABILITY", "0.2")
        ),
        service_known_address_probability=float(
            os.getenv("SERVICE_KNOWN_ADDRESS_PROBABILITY", "0.2")
        ),
        service_known_address_matches_probability=float(
            os.getenv("SERVICE_KNOWN_ADDRESS_MATCHES_PROBABILITY", "0.8")
        ),
        address_collection_followup_probability=float(
            os.getenv("ADDRESS_COLLECTION_FOLLOWUP_PROBABILITY", "0.35")
        ),
    )
