from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI, OpenAI

from multi_agent_data_synthesis.config import AppConfig


def extract_json_object(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("Model returned empty content.")

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Could not locate JSON object in: {text}")

    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("Parsed JSON is not an object.")
    return parsed


class OpenAIChatClient:
    def __init__(self, config: AppConfig):
        self.config = config
        self.client = OpenAI(
            base_url=config.openai_base_url,
            api_key=config.openai_api_key,
            timeout=config.request_timeout,
        )
        self.async_client = AsyncOpenAI(
            base_url=config.openai_base_url,
            api_key=config.openai_api_key,
            timeout=config.request_timeout,
        )

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int = 800,
        enable_thinking: bool = False,
    ) -> str:
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=self.config.default_temperature if temperature is None else temperature,
            max_tokens=max_tokens,
            extra_body={
                "enable_thinking": enable_thinking,
            }
        )
        content = response.choices[0].message.content
        return content or ""

    def complete_json(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int = 800,
        enable_thinking: bool = False,
    ) -> dict[str, Any]:
        text = self.complete(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            enable_thinking=enable_thinking,
        )
        try:
            return extract_json_object(text)
        except ValueError:
            retry_messages = messages + [
                {
                    "role": "user",
                    "content": "上一次输出不是合法 JSON。请仅返回一个 JSON 对象，不要附带解释。",
                }
            ]
            retry_text = self.complete(
                model=model,
                messages=retry_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return extract_json_object(retry_text)

    async def complete_async(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int = 800,
    ) -> str:
        response = await self.async_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=self.config.default_temperature if temperature is None else temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        return content or ""

    async def complete_json_async(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int = 800,
    ) -> dict[str, Any]:
        text = await self.complete_async(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        try:
            return extract_json_object(text)
        except ValueError:
            retry_messages = messages + [
                {
                    "role": "user",
                    "content": "上一次输出不是合法 JSON。请仅返回一个 JSON 对象，不要附带解释。",
                }
            ]
            retry_text = await self.complete_async(
                model=model,
                messages=retry_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return extract_json_object(retry_text)
