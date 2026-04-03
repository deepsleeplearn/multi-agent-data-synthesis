from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any


SUPPORTED_BRANDS = {"美的"}
SUPPORTED_CATEGORIES = {"空气能热水器", "空气能热水机"}

SLOT_DESCRIPTIONS = {
    "issue_description": "用户对故障或安装诉求的具体描述",
    "surname": "用户姓氏",
    "phone": "联系电话",
    "address": "详细上门地址",
    "product_model": "家电型号",
    "request_type": "诉求类型，通常为 fault 或 installation",
    "purchase_channel": "购买渠道",
    "availability": "用户可预约的上门时间",
    "phone_contactable": "当前来电号码是否可联系到用户",
    "phone_contact_owner": "登记号码归属，如本人、爱人、朋友等",
    "phone_collection_attempts": "拨号盘录入联系方式的尝试次数",
    "product_arrived": "安装场景下产品是否已到货",
}


@dataclass
class ProductProfile:
    brand: str
    category: str
    model: str
    purchase_channel: str = ""


@dataclass
class CustomerProfile:
    full_name: str
    surname: str
    phone: str
    address: str
    persona: str


@dataclass
class ServiceRequest:
    request_type: str
    issue: str
    desired_resolution: str
    availability: str = ""


@dataclass
class Scenario:
    scenario_id: str
    product: ProductProfile
    customer: CustomerProfile
    request: ServiceRequest
    hidden_context: dict[str, Any] = field(default_factory=dict)
    required_slots: list[str] = field(default_factory=list)
    max_turns: int = 20
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Scenario":
        scenario = cls(
            scenario_id=data["scenario_id"],
            product=ProductProfile(**data["product"]),
            customer=CustomerProfile(**data["customer"]),
            request=ServiceRequest(**data["request"]),
            hidden_context=dict(data.get("hidden_context", {})),
            required_slots=list(data.get("required_slots", [])),
            max_turns=int(data.get("max_turns", 20)),
            tags=list(data.get("tags", [])),
        )
        scenario.validate_domain()
        return scenario

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def clone_with_id(self, scenario_id: str) -> "Scenario":
        return replace(self, scenario_id=scenario_id)

    def with_generated_hidden_settings(
        self,
        *,
        customer: CustomerProfile,
        request: ServiceRequest,
        hidden_context: dict[str, Any],
    ) -> "Scenario":
        return replace(
            self,
            customer=customer,
            request=request,
            hidden_context=hidden_context,
        )

    def validate_domain(self) -> None:
        if self.product.brand not in SUPPORTED_BRANDS:
            raise ValueError(
                f"Unsupported brand '{self.product.brand}'. Only {sorted(SUPPORTED_BRANDS)} are allowed."
            )
        if self.product.category not in SUPPORTED_CATEGORIES:
            raise ValueError(
                "Unsupported category "
                f"'{self.product.category}'. Only {sorted(SUPPORTED_CATEGORIES)} are allowed."
            )


@dataclass
class DialogueTurn:
    speaker: str
    text: str
    round_index: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DialogueSample:
    scenario_id: str
    status: str
    rounds_used: int
    transcript: list[DialogueTurn]
    collected_slots: dict[str, str]
    missing_slots: list[str]
    scenario: dict[str, Any]
    validation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["dialogue_process"] = data["transcript"]
        data["dialogue_text"] = "\n".join(
            f"{turn['speaker']}: {turn['text']}" for turn in data["transcript"]
        )
        data["related_info"] = {
            "product": data["scenario"]["product"],
            "customer": data["scenario"]["customer"],
            "request": data["scenario"]["request"],
            "hidden_context": data["scenario"].get("hidden_context", {}),
            "required_slots": data["scenario"].get("required_slots", []),
            "collected_slots": data["collected_slots"],
            "missing_slots": data["missing_slots"],
            "status": data["status"],
            "validation": data["validation"],
        }
        return data


def effective_required_slots(scenario: Scenario) -> list[str]:
    skip_slots: set[str] = set()
    if scenario.request.request_type == "fault":
        skip_slots.update({"product_model", "availability"})
    if scenario.request.request_type == "installation":
        skip_slots.update({"product_model", "availability"})
    return [slot for slot in scenario.required_slots if slot not in skip_slots]
