from __future__ import annotations

import json
from typing import Any

import httpx

from multi_agent_data_synthesis.config import AppConfig, load_model_request_profiles


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

    def _build_headers(self, model: str) -> dict[str, str]:
        headers = {
            "Aimp-Biz-Id": model,
            "Authorization": f"Bearer {self.config.openai_api_key}",
            "Content-Type": "application/json",
        }
        if self.config.user.strip():
            headers["AIGC-USER"] = self.config.user.strip()
        return headers

    def _build_payload(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int | None,
        enable_thinking: bool = False,
    ) -> dict[str, Any]:
        profile = self._request_profile_for_model(model)
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        resolved_temperature = self.config.default_temperature if temperature is None else temperature
        if profile["include_temperature"] and resolved_temperature is not None:
            payload[str(profile["temperature_param"])] = resolved_temperature

        if profile["include_max_tokens"] and max_tokens is not None:
            payload[str(profile["max_tokens_param"])] = max_tokens

        if profile["include_enable_thinking"] and enable_thinking:
            payload[str(profile["enable_thinking_param"])] = True

        extra_body = profile.get("extra_body", {})
        if isinstance(extra_body, dict):
            payload.update(extra_body)

        return payload

    @staticmethod
    def _request_profile_for_model(model: str) -> dict[str, Any]:
        profiles = load_model_request_profiles()
        profile: dict[str, Any] = dict(profiles.get("default", {}))
        profile.update(profiles.get(model, {}))
        profile.setdefault("include_temperature", True)
        profile.setdefault("include_max_tokens", True)
        profile.setdefault("temperature_param", "temperature")
        profile.setdefault("max_tokens_param", "max_tokens")
        profile.setdefault("include_enable_thinking", True)
        profile.setdefault("enable_thinking_param", "enable_thinking")
        return profile

    @staticmethod
    def _extract_message_content(payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError(f"Model response missing choices: {payload}")

        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise ValueError(f"Model response missing message: {payload}")

        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    text_parts.append(item["text"])
                    continue
                if isinstance(item.get("content"), str):
                    text_parts.append(item["content"])
            return "".join(text_parts)
        return ""

    def _send_request(
        self,
        *,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        with httpx.Client(timeout=self.config.request_timeout) as client:
            response = client.post(self.config.openai_base_url, json=payload, headers=headers)
        if response.status_code >= 400:
            raise RuntimeError(
                f"Model request failed with status {response.status_code}: {response.text}"
            )
        return response.json()

    async def _send_request_async(
        self,
        *,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.config.request_timeout) as client:
            response = await client.post(self.config.openai_base_url, json=payload, headers=headers)
        if response.status_code >= 400:
            raise RuntimeError(
                f"Model request failed with status {response.status_code}: {response.text}"
            )
        return response.json()

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        enable_thinking: bool = False,
    ) -> str:
        payload = self._build_payload(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            enable_thinking=enable_thinking,
        )
        response = self._send_request(headers=self._build_headers(model), payload=payload)
        return self._extract_message_content(response)

    def complete_json(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
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
                enable_thinking=enable_thinking,
            )
            return extract_json_object(retry_text)

    async def complete_async(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        enable_thinking: bool = False,
    ) -> str:
        payload = self._build_payload(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            enable_thinking=enable_thinking,
        )
        response = await self._send_request_async(
            headers=self._build_headers(model),
            payload=payload,
        )
        return self._extract_message_content(response)

    async def complete_json_async(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        enable_thinking: bool = False,
    ) -> dict[str, Any]:
        text = await self.complete_async(
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
            retry_text = await self.complete_async(
                model=model,
                messages=retry_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                enable_thinking=enable_thinking,
            )
            return extract_json_object(retry_text)
