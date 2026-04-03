from __future__ import annotations

import random
import re
from dataclasses import dataclass

from multi_agent_data_synthesis.schemas import DialogueTurn, Scenario, effective_required_slots


MOBILE_PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")
PromptVariant = str | tuple[str, float]
PromptConfig = list[PromptVariant]


@dataclass
class ServiceRuntimeState:
    expected_contactable_confirmation: bool = False
    awaiting_phone_keypad_input: bool = False
    expected_phone_number_confirmation: bool = False
    phone_input_attempts: int = 0
    pending_phone_number_confirmation: str = ""
    expected_address_confirmation: bool = False
    expected_product_arrival_confirmation: bool = False
    product_arrival_checked: bool = False
    pending_address_confirmation: str = ""
    awaiting_full_address: bool = False
    address_input_attempts: int = 0


@dataclass
class ServicePolicyResult:
    reply: str
    slot_updates: dict[str, str]
    is_ready_to_close: bool


class ServiceDialoguePolicy:
    FAULT_ACKNOWLEDGEMENT_PREFIX = "非常抱歉，给您添麻烦了，我这就安排是否上门维修"

    SURNAME_PROMPT = "请问您贵姓"
    CONTACTABLE_PROMPT = "请问您当前这个来电号码能联系到您吗？"
    PHONE_KEYPAD_PROMPT = "请您在拨号盘上输入您的联系方式，并以#号键结束。"
    PHONE_KEYPAD_RETRY_PROMPT = "您输入的号码有误，请重新在拨号盘上输入您的联系方式，并以#号键结束"
    PHONE_CONFIRMATION_TEMPLATE = "号码是{phone}，对吗"
    ISSUE_PROMPT = "请您简单描述一下当前需要处理的问题或安装需求。"
    FAULT_ISSUE_PROMPT = "请问热水器现在是出现了什么问题？"
    ADDRESS_PROMPT = "需要登记下您的地址，麻烦你完整的说下省、市、区、乡镇，精确到门牌号。"
    ADDRESS_FOLLOWUP_PROMPT = "请再补充完整地址，需要包含省、市、区、乡镇，精确到门牌号。"
    ADDRESS_CONFIRMATION_TEMPLATE = "跟您确认一下，地址是{address}，对吗？"
    PRODUCT_ARRIVAL_PROMPT = "请问热水器到货了没？"
    PRODUCT_MODEL_PROMPT = "请问产品型号方便提供一下吗？"
    AVAILABILITY_PROMPT = "请问您方便预约什么时间上门？"
    PURCHASE_CHANNEL_PROMPT = "请问您是通过哪个渠道购买的呢？"
    CLOSING_PROMPT = "这边先帮您登记好了，后续会有师傅与您联系，请您保持电话畅通。"
    INSTALLATION_CLOSING_PROMPT = "这边先帮您登记好了，后续会有专人与您联系安装事宜，请您保持电话畅通。"

    # 每条话术支持配置为 [(文案, 权重), ...]，每次发送时使用 random.choices 按权重随机选择。
    SURNAME_PROMPT: PromptConfig = [("请问您贵姓", 1.0)]
    CONTACTABLE_PROMPT: PromptConfig = [("请问您当前这个来电号码能联系到您吗？", 1.0)]
    PHONE_KEYPAD_PROMPT: PromptConfig = [("请您在拨号盘上输入您的联系方式，并以#号键结束。", 1.0)]
    PHONE_KEYPAD_RETRY_PROMPT: PromptConfig = [
        ("您输入的号码有误，请重新在拨号盘上输入您的联系方式，并以#号键结束", 1.0)
    ]
    PHONE_CONFIRMATION_TEMPLATE: PromptConfig = [("号码是{phone}，对吗", 1.0)]
    ISSUE_PROMPT: PromptConfig = [("请您简单描述一下当前需要处理的问题或安装需求。", 1.0)]
    FAULT_ISSUE_PROMPT: PromptConfig = [("请问热水器现在是出现了什么问题？", 1.0)]
    ADDRESS_PROMPT: PromptConfig = [
        ("需要登记下您的地址，麻烦你完整的说下省、市、区、乡镇，精确到门牌号。", 1.0)
    ]
    ADDRESS_FOLLOWUP_PROMPT: PromptConfig = [
        ("请再补充完整地址，需要包含省、市、区、乡镇，精确到门牌号。", 1.0)
    ]
    ADDRESS_CONFIRMATION_TEMPLATE: PromptConfig = [("跟您确认一下，地址是{address}，对吗？", 1.0)]
    PRODUCT_ARRIVAL_PROMPT: PromptConfig = [("请问热水器到货了没？", 1.0)]
    PRODUCT_MODEL_PROMPT: PromptConfig = [("请问产品型号方便提供一下吗？", 1.0)]
    AVAILABILITY_PROMPT: PromptConfig = [("请问您方便预约什么时间上门？", 1.0)]
    PURCHASE_CHANNEL_PROMPT: PromptConfig = [("请问您是通过哪个渠道购买的呢？", 1.0)]
    CLOSING_PROMPT: PromptConfig = [("这边先帮您登记好了，后续会有师傅与您联系，请您保持电话畅通。", 1.0)]
    INSTALLATION_CLOSING_PROMPT: PromptConfig = [
        ("这边先帮您登记好了，后续会有专人与您联系安装事宜，请您保持电话畅通。", 1.0)
    ]

    def __init__(
        self,
        ok_prefix_probability: float = 1.0,
        rng: random.Random | None = None,
    ):
        self.ok_prefix_probability = max(0.0, min(1.0, ok_prefix_probability))
        self.rng = rng or random.Random()

    def respond(
        self,
        *,
        scenario: Scenario,
        transcript: list[DialogueTurn],
        collected_slots: dict[str, str],
        runtime_state: ServiceRuntimeState,
    ) -> ServicePolicyResult:
        if not any(turn.speaker == "service" for turn in transcript):
            return ServicePolicyResult(
                reply=self._build_opening_prompt(scenario),
                slot_updates={},
                is_ready_to_close=False,
            )

        last_user_turn = self._last_turn_by_speaker(transcript, "user")
        if last_user_turn is None:
            return ServicePolicyResult(reply="", slot_updates={}, is_ready_to_close=False)

        previous_service_text = self._previous_service_text(transcript)
        previous_service_signature = self._normalize_prompt_text(previous_service_text)
        slot_updates = self._extract_standard_slots(
            scenario=scenario,
            previous_service_signature=previous_service_signature,
            user_text=last_user_turn.text,
            collected_slots=collected_slots,
        )
        required_slots = effective_required_slots(scenario)
        merged_slots = dict(collected_slots)
        merged_slots.update(slot_updates)

        if runtime_state.expected_contactable_confirmation:
            return self._handle_contactable_confirmation(
                scenario=scenario,
                user_text=last_user_turn.text,
                collected_slots=merged_slots,
                runtime_state=runtime_state,
            )

        if runtime_state.awaiting_phone_keypad_input:
            return self._handle_phone_keypad_input(
                scenario=scenario,
                user_text=last_user_turn.text,
                collected_slots=merged_slots,
                runtime_state=runtime_state,
            )

        if runtime_state.expected_phone_number_confirmation:
            return self._handle_phone_number_confirmation(
                scenario=scenario,
                user_text=last_user_turn.text,
                collected_slots=merged_slots,
                runtime_state=runtime_state,
            )

        if runtime_state.expected_address_confirmation:
            return self._handle_address_confirmation(
                scenario=scenario,
                user_text=last_user_turn.text,
                collected_slots=merged_slots,
                runtime_state=runtime_state,
                slot_updates=slot_updates,
            )

        if runtime_state.expected_product_arrival_confirmation:
            return self._handle_product_arrival_confirmation(
                scenario=scenario,
                user_text=last_user_turn.text,
                slot_updates=slot_updates,
                runtime_state=runtime_state,
            )

        if runtime_state.awaiting_full_address:
            return self._handle_full_address_input(
                scenario=scenario,
                user_text=last_user_turn.text,
                collected_slots=merged_slots,
                runtime_state=runtime_state,
                slot_updates=slot_updates,
            )

        next_slot = self._next_slot_to_request(
            merged_slots,
            required_slots,
        )
        if not next_slot:
            if scenario.request.request_type == "installation" and not runtime_state.product_arrival_checked:
                return self._start_product_arrival_confirmation(runtime_state=runtime_state)
            return ServicePolicyResult(
                reply=self._closing_prompt_for_scenario(scenario),
                slot_updates=slot_updates,
                is_ready_to_close=True,
            )

        if next_slot == "phone":
            runtime_state.expected_contactable_confirmation = True

            if next_slot == "address":
                known_address = self._service_known_address_value(scenario)
                if known_address:
                    return self._start_address_confirmation(
                        runtime_state=runtime_state,
                        address=known_address,
                        slot_updates=slot_updates,
                    )
                runtime_state.awaiting_full_address = True
                runtime_state.address_input_attempts = 0

        return ServicePolicyResult(
            reply=self._reply_for_next_slot(
                scenario=scenario,
                collected_slots=collected_slots,
                slot_updates=slot_updates,
                next_slot=next_slot,
            ),
            slot_updates=slot_updates,
            is_ready_to_close=False,
        )

    def _handle_contactable_confirmation(
        self,
        *,
        scenario: Scenario,
        user_text: str,
        collected_slots: dict[str, str],
        runtime_state: ServiceRuntimeState,
    ) -> ServicePolicyResult:
        intent = self._classify_yes_no(user_text)
        runtime_state.expected_contactable_confirmation = False

        if intent == "yes":
            slot_updates = {
                "phone": scenario.customer.phone,
                "phone_contactable": "yes",
                "phone_contact_owner": "本人当前来电",
                "phone_collection_attempts": "0",
            }
            merged_slots = dict(collected_slots)
            merged_slots.update(slot_updates)
            next_slot = self._next_slot_to_request(merged_slots, effective_required_slots(scenario))
            if not next_slot:
                if scenario.request.request_type == "installation" and not runtime_state.product_arrival_checked:
                    return self._start_product_arrival_confirmation(
                        runtime_state=runtime_state,
                        slot_updates=slot_updates,
                    )
                return ServicePolicyResult(
                    reply=self._closing_prompt_for_scenario(scenario),
                    slot_updates=slot_updates,
                    is_ready_to_close=True,
                )
            if next_slot == "address":
                known_address = self._service_known_address_value(scenario)
                if known_address:
                    return self._start_address_confirmation(
                        runtime_state=runtime_state,
                        address=known_address,
                        slot_updates=slot_updates,
                    )
                runtime_state.awaiting_full_address = True
                runtime_state.address_input_attempts = 0
            return ServicePolicyResult(
                reply=self._reply_for_next_slot(
                    scenario=scenario,
                    collected_slots=collected_slots,
                    slot_updates=slot_updates,
                    next_slot=next_slot,
                ),
                slot_updates=slot_updates,
                is_ready_to_close=False,
            )

        if intent == "no":
            runtime_state.awaiting_phone_keypad_input = True
            runtime_state.phone_input_attempts = 0
            slot_updates = {"phone_contactable": "no"}
            owner = self._contact_phone_owner(scenario)
            if owner:
                slot_updates["phone_contact_owner"] = owner
            return ServicePolicyResult(
                reply=self._phone_keypad_prompt(),
                slot_updates=slot_updates,
                is_ready_to_close=False,
            )

        runtime_state.expected_contactable_confirmation = True
        return ServicePolicyResult(
            reply=self._contactable_prompt(),
            slot_updates={},
            is_ready_to_close=False,
        )

    def _handle_phone_number_confirmation(
        self,
        *,
        scenario: Scenario,
        user_text: str,
        collected_slots: dict[str, str],
        runtime_state: ServiceRuntimeState,
    ) -> ServicePolicyResult:
        intent = self._classify_yes_no(user_text)
        pending_phone = runtime_state.pending_phone_number_confirmation

        if intent == "yes" and pending_phone:
            runtime_state.expected_phone_number_confirmation = False
            runtime_state.pending_phone_number_confirmation = ""
            slot_updates = {
                "phone": pending_phone,
                "phone_collection_attempts": str(runtime_state.phone_input_attempts),
            }
            owner = self._contact_phone_owner(scenario)
            if owner:
                slot_updates.setdefault("phone_contact_owner", owner)
            merged_slots = dict(collected_slots)
            merged_slots.update(slot_updates)
            next_slot = self._next_slot_to_request(merged_slots, effective_required_slots(scenario))
            if not next_slot:
                if scenario.request.request_type == "installation" and not runtime_state.product_arrival_checked:
                    return self._start_product_arrival_confirmation(
                        runtime_state=runtime_state,
                        slot_updates=slot_updates,
                    )
                return ServicePolicyResult(
                    reply=self._closing_prompt_for_scenario(scenario),
                    slot_updates=slot_updates,
                    is_ready_to_close=True,
                )
            if next_slot == "address":
                known_address = self._service_known_address_value(scenario)
                if known_address:
                    return self._start_address_confirmation(
                        runtime_state=runtime_state,
                        address=known_address,
                        slot_updates=slot_updates,
                    )
                runtime_state.awaiting_full_address = True
                runtime_state.address_input_attempts = 0
            return ServicePolicyResult(
                reply=self._prompt_for_slot(next_slot, scenario),
                slot_updates=slot_updates,
                is_ready_to_close=False,
            )

        if intent == "no":
            runtime_state.expected_phone_number_confirmation = False
            runtime_state.pending_phone_number_confirmation = ""
            runtime_state.awaiting_phone_keypad_input = True
            return ServicePolicyResult(
                reply=self._phone_keypad_prompt(),
                slot_updates={
                    "phone_collection_attempts": str(runtime_state.phone_input_attempts),
                },
                is_ready_to_close=False,
            )

        runtime_state.expected_phone_number_confirmation = True
        return ServicePolicyResult(
            reply=self._phone_confirmation_prompt(pending_phone),
            slot_updates={},
            is_ready_to_close=False,
        )

    def _handle_address_confirmation(
        self,
        *,
        scenario: Scenario,
        user_text: str,
        collected_slots: dict[str, str],
        runtime_state: ServiceRuntimeState,
        slot_updates: dict[str, str],
    ) -> ServicePolicyResult:
        intent = self._classify_yes_no(user_text)
        runtime_state.expected_address_confirmation = False
        confirmation_address = (
            runtime_state.pending_address_confirmation
            or self._service_known_address_value(scenario)
            or scenario.customer.address
        )

        if intent == "yes":
            slot_updates = dict(slot_updates)
            slot_updates["address"] = scenario.customer.address
            runtime_state.pending_address_confirmation = ""
            merged_slots = dict(collected_slots)
            merged_slots.update(slot_updates)
            next_slot = self._next_slot_to_request(merged_slots, effective_required_slots(scenario))
            if not next_slot:
                if scenario.request.request_type == "installation" and not runtime_state.product_arrival_checked:
                    return self._start_product_arrival_confirmation(
                        runtime_state=runtime_state,
                        slot_updates=slot_updates,
                    )
                return ServicePolicyResult(
                    reply=self._closing_prompt_for_scenario(scenario),
                    slot_updates=slot_updates,
                    is_ready_to_close=True,
                )
            if next_slot == "phone":
                runtime_state.expected_contactable_confirmation = True
            return ServicePolicyResult(
                reply=self._reply_for_next_slot(
                    scenario=scenario,
                    collected_slots=collected_slots,
                    slot_updates=slot_updates,
                    next_slot=next_slot,
                ),
                slot_updates=slot_updates,
                is_ready_to_close=False,
            )

        if intent == "no":
            runtime_state.awaiting_full_address = True
            runtime_state.address_input_attempts = 0
            runtime_state.pending_address_confirmation = ""
            return ServicePolicyResult(
                reply=self._address_prompt(),
                slot_updates=slot_updates,
                is_ready_to_close=False,
            )

        return self._start_address_confirmation(
            runtime_state=runtime_state,
            address=confirmation_address,
            slot_updates=slot_updates,
        )

    def _handle_phone_keypad_input(
        self,
        *,
        scenario: Scenario,
        user_text: str,
        collected_slots: dict[str, str],
        runtime_state: ServiceRuntimeState,
    ) -> ServicePolicyResult:
        runtime_state.phone_input_attempts += 1
        digits = re.sub(r"\D", "", user_text or "")
        slot_updates = {
            "phone_collection_attempts": str(runtime_state.phone_input_attempts),
        }

        if MOBILE_PHONE_PATTERN.match(digits):
            runtime_state.awaiting_phone_keypad_input = False
            runtime_state.expected_phone_number_confirmation = True
            runtime_state.pending_phone_number_confirmation = digits
            return ServicePolicyResult(
                reply=self._phone_confirmation_prompt(digits),
                slot_updates=slot_updates,
                is_ready_to_close=False,
            )

        if runtime_state.phone_input_attempts < 3:
            return ServicePolicyResult(
                reply=self._phone_keypad_retry_prompt(),
                slot_updates=slot_updates,
                is_ready_to_close=False,
            )
        return ServicePolicyResult(
            reply=self._phone_keypad_retry_prompt(),
            slot_updates=slot_updates,
            is_ready_to_close=False,
        )

    def _handle_full_address_input(
        self,
        *,
        scenario: Scenario,
        user_text: str,
        collected_slots: dict[str, str],
        runtime_state: ServiceRuntimeState,
        slot_updates: dict[str, str],
    ) -> ServicePolicyResult:
        runtime_state.address_input_attempts += 1
        prepared_address = self._prepare_address_for_confirmation(user_text)
        address_candidate = self._normalize_address_text(prepared_address)

        if self._is_complete_address(address_candidate, scenario.customer.address):
            runtime_state.awaiting_full_address = False
            return self._start_address_confirmation(
                runtime_state=runtime_state,
                address=prepared_address,
                slot_updates=slot_updates,
            )

        return ServicePolicyResult(
            reply=self._address_followup_prompt(),
            slot_updates=slot_updates,
            is_ready_to_close=False,
        )

    def _handle_product_arrival_confirmation(
        self,
        *,
        scenario: Scenario,
        user_text: str,
        slot_updates: dict[str, str],
        runtime_state: ServiceRuntimeState,
    ) -> ServicePolicyResult:
        intent = self._classify_yes_no(user_text)

        if intent not in {"yes", "no"}:
            runtime_state.expected_product_arrival_confirmation = True
            return ServicePolicyResult(
                reply=self._product_arrival_prompt(),
                slot_updates=slot_updates,
                is_ready_to_close=False,
            )

        runtime_state.expected_product_arrival_confirmation = False
        runtime_state.product_arrival_checked = True
        slot_updates = dict(slot_updates)
        slot_updates["product_arrived"] = "yes" if intent == "yes" else "no"
        return ServicePolicyResult(
            reply=self._closing_prompt_for_scenario(scenario),
            slot_updates=slot_updates,
            is_ready_to_close=True,
        )

    def _extract_standard_slots(
        self,
        *,
        scenario: Scenario,
        previous_service_signature: str,
        user_text: str,
        collected_slots: dict[str, str],
    ) -> dict[str, str]:
        slot_updates: dict[str, str] = {}

        if (
            "issue_description" in collected_slots
            and not collected_slots["issue_description"].strip()
            and user_text.strip()
        ):
            if previous_service_signature == self._normalize_prompt_text(self._build_opening_prompt(scenario)):
                if self._opening_response_contains_issue_detail(user_text):
                    slot_updates["issue_description"] = user_text.strip()
            elif previous_service_signature in (
                self._prompt_signatures(self.ISSUE_PROMPT)
                | self._prompt_signatures(self.FAULT_ISSUE_PROMPT)
            ):
                slot_updates["issue_description"] = user_text.strip()

        if (
            "request_type" in collected_slots
            and not collected_slots["request_type"].strip()
            and previous_service_signature == self._normalize_prompt_text(self._build_opening_prompt(scenario))
        ):
            slot_updates["request_type"] = scenario.request.request_type

        if (
            "surname" in collected_slots
            and not collected_slots["surname"].strip()
            and previous_service_signature in self._prompt_signatures(self.SURNAME_PROMPT)
            and scenario.customer.surname in user_text
        ):
            slot_updates["surname"] = scenario.customer.surname

        if (
            "product_model" in collected_slots
            and not collected_slots["product_model"].strip()
            and previous_service_signature in self._prompt_signatures(self.PRODUCT_MODEL_PROMPT)
            and scenario.product.model in user_text
        ):
            slot_updates["product_model"] = scenario.product.model

        if (
            "availability" in collected_slots
            and not collected_slots["availability"].strip()
            and previous_service_signature in self._prompt_signatures(self.AVAILABILITY_PROMPT)
            and scenario.request.availability
            and scenario.request.availability in user_text
        ):
            slot_updates["availability"] = scenario.request.availability

        if (
            "purchase_channel" in collected_slots
            and not collected_slots["purchase_channel"].strip()
            and previous_service_signature in self._prompt_signatures(self.PURCHASE_CHANNEL_PROMPT)
            and scenario.product.purchase_channel
            and scenario.product.purchase_channel in user_text
        ):
            slot_updates["purchase_channel"] = scenario.product.purchase_channel

        return slot_updates

    def _next_slot_to_request(
        self,
        collected_slots: dict[str, str],
        required_slots: list[str],
        skip_slots: set[str] | None = None,
    ) -> str | None:
        skip_slots = skip_slots or set()
        priority = [
            "issue_description",
            "surname",
            "phone",
            "address",
            "product_model",
            "purchase_channel",
            "availability",
            "request_type",
        ]
        for slot in priority:
            if (
                slot in required_slots
                and slot not in skip_slots
                and not collected_slots.get(slot, "").strip()
            ):
                return slot
        for slot in required_slots:
            if slot not in skip_slots and not collected_slots.get(slot, "").strip():
                return slot
        return None

    def _prompt_for_slot(self, slot: str, scenario: Scenario) -> str:
        prompts = {
            "issue_description": self._fault_issue_prompt()
            if scenario.request.request_type == "fault"
            else self._issue_prompt(),
            "surname": self._surname_prompt(),
            "phone": self._contactable_prompt(),
            "address": self._address_prompt(),
            "product_model": self._product_model_prompt(),
            "purchase_channel": self._purchase_channel_prompt(),
            "availability": self._availability_prompt(),
            "request_type": self._issue_prompt(),
        }
        return prompts.get(slot, self._issue_prompt())

    def _reply_for_next_slot(
        self,
        *,
        scenario: Scenario,
        collected_slots: dict[str, str],
        slot_updates: dict[str, str],
        next_slot: str,
    ) -> str:
        reply = self._prompt_for_slot(next_slot, scenario)
        if self._should_prepend_fault_acknowledgement(
            scenario=scenario,
            collected_slots=collected_slots,
            slot_updates=slot_updates,
        ):
            return self._prepend_fault_acknowledgement(reply)
        return reply

    def _should_prepend_fault_acknowledgement(
        self,
        *,
        scenario: Scenario,
        collected_slots: dict[str, str],
        slot_updates: dict[str, str],
    ) -> bool:
        return (
            scenario.request.request_type == "fault"
            and not collected_slots.get("issue_description", "").strip()
            and bool(slot_updates.get("issue_description", "").strip())
        )

    def _prepend_fault_acknowledgement(self, reply: str) -> str:
        normalized_reply = re.sub(r"^好的[，,\s]*", "", (reply or "").strip())
        if not normalized_reply:
            return self.FAULT_ACKNOWLEDGEMENT_PREFIX
        return f"{self.FAULT_ACKNOWLEDGEMENT_PREFIX}，{normalized_reply}"

    def _closing_prompt_for_scenario(self, scenario: Scenario) -> str:
        if scenario.request.request_type == "installation":
            return self._with_optional_ok_prefix(self._choose_prompt_text(self.INSTALLATION_CLOSING_PROMPT))
        return self._with_optional_ok_prefix(self._choose_prompt_text(self.CLOSING_PROMPT))

    def _build_opening_prompt(self, scenario: Scenario) -> str:
        action = "维修" if scenario.request.request_type == "fault" else "安装"
        return f"您好，很高兴为您服务，请问是美的空气能热水器需要{action}吗？"

    @staticmethod
    def _last_turn_by_speaker(
        transcript: list[DialogueTurn],
        speaker: str,
    ) -> DialogueTurn | None:
        for turn in reversed(transcript):
            if turn.speaker == speaker:
                return turn
        return None

    @staticmethod
    def _previous_service_text(transcript: list[DialogueTurn]) -> str:
        if len(transcript) < 2:
            return ""
        previous_turn = transcript[-2]
        return previous_turn.text if previous_turn.speaker == "service" else ""

    @staticmethod
    def _classify_yes_no(text: str) -> str | None:
        normalized = (text or "").replace("，", "").replace("。", "").replace(" ", "")
        negative_keywords = (
            "不能",
            "不行",
            "联系不到",
            "联系不上",
            "打不到",
            "打不通",
            "不是",
            "不对",
            "不太对",
            "不准确",
            "不完全对",
            "有误",
            "错了",
            "没到",
            "还没到",
            "未到",
            "否",
        )
        positive_keywords = (
            "可以",
            "能联系",
            "能打通",
            "是的",
            "对",
            "对的",
            "就是这个",
            "没错",
            "正确",
            "到了",
            "到货了",
            "已经到了",
            "已经到货",
            "可以联系",
            "行",
            "嗯",
        )

        if any(keyword in normalized for keyword in negative_keywords):
            return "no"
        if any(keyword in normalized for keyword in positive_keywords):
            return "yes"
        return None

    @classmethod
    def _opening_response_contains_issue_detail(cls, text: str) -> bool:
        normalized = (text or "").strip()
        if not normalized:
            return False
        compact = re.sub(r"[，。！？、,.!\s]", "", normalized)
        positive_only_patterns = (
            r"^(对|对的|是|是的|嗯|嗯嗯|哎对|对啊|好|好的|没错|对没错)+$",
        )
        if any(re.fullmatch(pattern, compact) for pattern in positive_only_patterns):
            return False
        if cls._classify_yes_no(normalized) == "yes" and len(compact) <= 6:
            return False
        return True

    @staticmethod
    def _contact_phone_owner(scenario: Scenario) -> str:
        value = scenario.hidden_context.get("contact_phone_owner", "")
        return str(value).strip()

    @staticmethod
    def _service_known_address_value(scenario: Scenario) -> str:
        if not bool(scenario.hidden_context.get("service_known_address", False)):
            return ""
        value = scenario.hidden_context.get("service_known_address_value", "")
        return str(value).strip()

    def _start_product_arrival_confirmation(
        self,
        *,
        runtime_state: ServiceRuntimeState,
        slot_updates: dict[str, str] | None = None,
    ) -> ServicePolicyResult:
        runtime_state.expected_product_arrival_confirmation = True
        return ServicePolicyResult(
            reply=self._product_arrival_prompt(),
            slot_updates=slot_updates or {},
            is_ready_to_close=False,
        )

    def _start_address_confirmation(
        self,
        *,
        runtime_state: ServiceRuntimeState,
        address: str,
        slot_updates: dict[str, str],
    ) -> ServicePolicyResult:
        runtime_state.expected_address_confirmation = True
        runtime_state.awaiting_full_address = False
        runtime_state.pending_address_confirmation = address
        return ServicePolicyResult(
            reply=self._address_confirmation_prompt(address),
            slot_updates=slot_updates,
            is_ready_to_close=False,
        )

    @staticmethod
    def _prepare_address_for_confirmation(text: str) -> str:
        cleaned = (text or "").strip().strip("，,。！？!?")
        prefix_patterns = (
            r"^(好的[，,\s]*)?地址是",
            r"^(好的[，,\s]*)?我家地址是",
            r"^(好的[，,\s]*)?详细地址是",
            r"^(好的[，,\s]*)?我的地址是",
        )
        for pattern in prefix_patterns:
            cleaned = re.sub(pattern, "", cleaned)
        cleaned = re.split(r"[。！？!?]", cleaned, maxsplit=1)[0]
        cleaned = re.split(r"[，,]\s*(?:麻烦|另外|还有|辛苦|谢谢|尽快|催一下|师傅)", cleaned, maxsplit=1)[0]
        return cleaned.strip().strip("，,。！？!?")

    @staticmethod
    def _normalize_address_text(text: str) -> str:
        return (
            (text or "")
            .replace("，", "")
            .replace(",", "")
            .replace("。", "")
            .replace(" ", "")
            .strip()
        )

    @classmethod
    def _is_complete_address(cls, candidate: str, actual_address: str) -> bool:
        if not candidate:
            return False
        normalized_actual = cls._normalize_address_text(actual_address)
        if candidate == normalized_actual:
            return True
        required_markers = ("省", "市", "区")
        has_required_markers = all(marker in candidate for marker in required_markers)
        has_house_number = bool(re.search(r"\d+", candidate))
        return (
            has_required_markers
            and has_house_number
            and len(candidate) >= max(10, len(normalized_actual) // 2)
        )

    @staticmethod
    def _normalize_prompt_text(text: str) -> str:
        normalized = (text or "").strip()
        normalized = re.sub(r"^好的[，,\s]*", "", normalized)
        return normalized.rstrip("。！？!?")

    @staticmethod
    def _resolve_prompt_variants(prompt_config: str | PromptConfig) -> tuple[list[str], list[float]]:
        if isinstance(prompt_config, str):
            return [prompt_config], [1.0]

        texts: list[str] = []
        weights: list[float] = []
        for variant in prompt_config:
            if isinstance(variant, str):
                texts.append(variant)
                weights.append(1.0)
                continue

            text, weight = variant
            texts.append(text)
            weights.append(max(0.0, float(weight)))

        if not texts:
            raise ValueError("Prompt variants must not be empty.")
        if sum(weights) <= 0:
            weights = [1.0] * len(texts)
        return texts, weights

    @classmethod
    def _prompt_signatures(cls, prompt_config: str | PromptConfig) -> set[str]:
        texts, _ = cls._resolve_prompt_variants(prompt_config)
        return {cls._normalize_prompt_text(text) for text in texts if text.strip()}

    @classmethod
    def summarize_prompt_variants(
        cls,
        prompt_config: str | PromptConfig,
        *,
        limit: int = 3,
        **format_kwargs: str,
    ) -> str:
        texts, _ = cls._resolve_prompt_variants(prompt_config)
        rendered_texts = [
            text.format(**format_kwargs) if format_kwargs else text for text in texts[: max(1, limit)]
        ]
        return "、".join(f"“{text}”" for text in rendered_texts if text)

    @classmethod
    def summarize_prompt_variants(
        cls,
        prompt_config: str | PromptConfig,
        *,
        limit: int = 3,
        **format_kwargs: str,
    ) -> str:
        texts, _ = cls._resolve_prompt_variants(prompt_config)
        rendered_texts = [
            text.format(**format_kwargs) if format_kwargs else text for text in texts[: max(1, limit)]
        ]
        return " / ".join(f'"{text}"' for text in rendered_texts if text)

    @classmethod
    def is_phone_keypad_prompt(cls, text: str) -> bool:
        normalized = cls._normalize_prompt_text(text)
        return normalized in cls._prompt_signatures(cls.PHONE_KEYPAD_PROMPT) or normalized in cls._prompt_signatures(
            cls.PHONE_KEYPAD_RETRY_PROMPT
        )

    @classmethod
    def is_address_collection_prompt(cls, text: str) -> bool:
        normalized = cls._normalize_prompt_text(text)
        return normalized in cls._prompt_signatures(cls.ADDRESS_PROMPT) or normalized in cls._prompt_signatures(
            cls.ADDRESS_FOLLOWUP_PROMPT
        )

    def _choose_prompt_text(self, prompt_config: str | PromptConfig, **format_kwargs: str) -> str:
        texts, weights = self._resolve_prompt_variants(prompt_config)
        selected = self.rng.choices(texts, weights=weights, k=1)[0]
        return selected.format(**format_kwargs) if format_kwargs else selected

    def _with_optional_ok_prefix(self, text: str) -> str:
        normalized = text.strip()
        if not normalized or normalized.startswith("好的"):
            return normalized
        if self.rng.random() < self.ok_prefix_probability:
            return f"好的，{normalized}"
        return normalized

    def _surname_prompt(self) -> str:
        return self._with_optional_ok_prefix(self._choose_prompt_text(self.SURNAME_PROMPT))

    def _contactable_prompt(self) -> str:
        return self._choose_prompt_text(self.CONTACTABLE_PROMPT)

    def _phone_keypad_prompt(self) -> str:
        return self._with_optional_ok_prefix(self._choose_prompt_text(self.PHONE_KEYPAD_PROMPT))

    def _phone_keypad_retry_prompt(self) -> str:
        return self._choose_prompt_text(self.PHONE_KEYPAD_RETRY_PROMPT)

    def _phone_confirmation_prompt(self, phone: str) -> str:
        return self._with_optional_ok_prefix(self._choose_prompt_text(self.PHONE_CONFIRMATION_TEMPLATE, phone=phone))

    def _issue_prompt(self) -> str:
        return self._choose_prompt_text(self.ISSUE_PROMPT)

    def _fault_issue_prompt(self) -> str:
        return self._with_optional_ok_prefix(self._choose_prompt_text(self.FAULT_ISSUE_PROMPT))

    def _address_prompt(self) -> str:
        return self._with_optional_ok_prefix(self._choose_prompt_text(self.ADDRESS_PROMPT))

    def _address_followup_prompt(self) -> str:
        return self._choose_prompt_text(self.ADDRESS_FOLLOWUP_PROMPT)

    def _address_confirmation_prompt(self, address: str) -> str:
        return self._with_optional_ok_prefix(
            self._choose_prompt_text(self.ADDRESS_CONFIRMATION_TEMPLATE, address=address)
        )

    def _product_arrival_prompt(self) -> str:
        return self._with_optional_ok_prefix(self._choose_prompt_text(self.PRODUCT_ARRIVAL_PROMPT))

    def _product_model_prompt(self) -> str:
        return self._choose_prompt_text(self.PRODUCT_MODEL_PROMPT)

    def _availability_prompt(self) -> str:
        return self._choose_prompt_text(self.AVAILABILITY_PROMPT)

    def _purchase_channel_prompt(self) -> str:
        return self._choose_prompt_text(self.PURCHASE_CHANNEL_PROMPT)
