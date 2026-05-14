from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import requests


DEFAULT_IE_BASE_URL = "https://aimpapi.midea.com/t-aigc/c-css-mcagent-ie-llm/v1/chat/completions"
DEFAULT_IE_BIZ_ID = "c-css-mcagent-ie-llm"
DEFAULT_IE_APIKEY = "msk-129ce5f2dc945f365a4ca6ee954f0524dc5b067b375cd4453cb0835a67ecc9d3"
DEFAULT_MODEL = "/model"
DEFAULT_TIMEOUT_SECONDS = 30

ADDRESS_SYSTEM_PROMPT = (
    "你是一个顶级的地址信息处理专家。你的任务是分析【机器人】和【用户】之间的对话，"
    "并根据用户的回应，严格遵循规则，推断出最终的、最准确的地址。"
    "你的回答必须且只能是一个严格的JSON格式字符串，"
    "格式为：{\"serviceAddress\":\"提取出的最终地址或无法判断\"}"
)

DEFAULT_DIALOGUE = [
    "用户: 小天鹅洗衣机需要维修",
    "客服: 您好，很高兴为您服务，请问是小天鹅洗衣机需要维修吗？",
    "用户: 是。",
    "客服: 好的，请问洗衣机是波轮、滚筒、还是复式的呢？",
    "用户: 嗯。",
    "客服: 请问洗衣机是上开盖的、侧开盖的、还是复式的呢？",
    "用户: 侧开盖的。",
    "客服: 好的，请问洗衣机现在是出现了什么问题？",
    "用户: 嗯，那是洗衣机还系统乱了，好像是洗涂啦啦的，是15分钟，再停时候还不停，还显示一个字母。",
    "客服: 非常抱歉，给您添麻烦了，我帮您安排售后处理。请问您贵姓啊？",
    "用户: 我姓康。",
    "客服: 好的，请问上门服务是联系您本次的来电号码吗？",
    "用户: 嗯。",
    "客服: 请问您本次服务地址是：山东省临沂市莒南县十字路街道国鑫佳苑1号楼4单元4层402室，对吗？",
    "用户: 对，莒南县。",
]


def _build_payload(*, model: str, dialogue: list[str]) -> dict[str, Any]:
    dialogue_text = "\n".join(dialogue)
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": ADDRESS_SYSTEM_PROMPT},
            {"role": "user", "content": f"<conversation>{dialogue_text}</conversation>\n"},
        ],
        "temperature": 0,
    }


def _extract_message_content(response_payload: dict[str, Any]) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return ""
    message = first_choice.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    return content if isinstance(content, str) else ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Request customer-agent IE address extraction API.")
    parser.add_argument("--url", default=os.getenv("IE_BASE_URL", DEFAULT_IE_BASE_URL))
    parser.add_argument("--apikey", default=os.getenv("IE_APIKEY", DEFAULT_IE_APIKEY))
    parser.add_argument("--biz-id", default=os.getenv("IE_BIZ_ID", DEFAULT_IE_BIZ_ID))
    parser.add_argument("--model", default=os.getenv("IE_MODEL", DEFAULT_MODEL))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("IE_TIMEOUT", DEFAULT_TIMEOUT_SECONDS)))
    args = parser.parse_args()

    payload = _build_payload(model=args.model, dialogue=DEFAULT_DIALOGUE)
    headers = {
        "Aimp-Biz-Id": args.biz_id,
        "Authorization": f"Bearer {args.apikey}",
        "Content-Type": "application/json",
    }

    print("request url:", args.url)
    print("request headers:", json.dumps({**headers, "Authorization": "<redacted>"}, ensure_ascii=False))
    print("request body:", json.dumps(payload, ensure_ascii=False, indent=2))

    response = requests.post(args.url, headers=headers, json=payload, timeout=args.timeout)
    print("response status:", response.status_code)
    print("response body:", response.text)
    response.raise_for_status()

    response_payload = response.json()
    content = _extract_message_content(response_payload)
    if content:
        print("choices[0].message.content:", content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
