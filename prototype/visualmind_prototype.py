#!/usr/bin/env python3
"""VisualMind Prototype 0.2.3 — local intelligent creative reasoning proof.

The prototype intentionally uses no external AI provider. It demonstrates the
CIM decision chain and uses a deterministic SVG renderer as a replaceable
Generator implementation.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import textwrap
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path


NO_RESEARCH = "No additional research supplied."

RU_FIELD_LABELS = {
    "request": "запрос пользователя",
    "objective": "цель",
    "audience": "целевая аудитория",
    "brand": "бренд",
    "product": "конкретный продукт или услуга",
    "asset_type": "тип цифрового материала",
    "expected_action": "ожидаемое действие зрителя",
    "trust_evidence": "утверждённые основания доверия",
    "research": "сводка исследования",
    "format": "канал и формат",
}

RU_DIRECTION_IDS = {
    "prevention": "профилактика",
    "product": "продукт",
    "trust": "доверие",
}


class DecisionState(str, Enum):
    DRAFT = "Draft"
    CONFIRMED = "Confirmed"
    REVISED = "Revised"


class WorkflowBlocked(RuntimeError):
    """Raised when professional reasoning cannot continue without facts."""


@dataclass
class ProjectContext:
    request: str
    objective: str
    audience: str
    brand: str
    product: str
    asset_type: str
    expected_action: str
    topic: str = ""
    channel: str = ""
    width: int = 0
    height: int = 0
    display_cta: str = ""
    display_cta_confirmed: bool = False
    trust_evidence: str = ""
    research: str = NO_RESEARCH


@dataclass(frozen=True)
class ParsedRequest:
    brand: str
    product: str
    audience: str
    topic: str
    expected_action: str
    display_cta: str
    asset_type: str


@dataclass
class KnowledgeGap:
    field: str
    question: str
    reason: str
    blocking: bool


@dataclass
class SemanticModel:
    brand: str
    offer: str
    topic: str
    audience: str
    objective: str
    expected_action: str
    audience_need: str
    trust_basis: str
    factual_basis: str


@dataclass
class CreativeDirection:
    direction_id: str
    name: str
    core_idea: str
    hero: str
    visual_strategy: str
    emotional_strategy: str
    rationale: str
    risk: str


@dataclass
class Decision:
    decision_id: str
    area: str
    statement: str
    rationale: str
    source_references: list[str]
    constraints: list[str]
    assumptions: list[str]
    risks: list[str]
    state: DecisionState = DecisionState.DRAFT
    user_confirmation: str = "Not confirmed"


@dataclass
class CreativeSpecification:
    semantic_model: SemanticModel
    selected_direction: CreativeDirection
    decisions: dict[str, Decision]

    def confirmed(self) -> bool:
        return bool(self.decisions) and all(
            decision.state == DecisionState.CONFIRMED
            for decision in self.decisions.values()
        )


@dataclass
class StructuredResult:
    source: str
    purpose: str
    content: CreativeSpecification
    confidence: str
    constraints: list[str]
    assumptions: list[str]
    risks: list[str]
    metadata: dict[str, str]


@dataclass
class GenerationSpecification:
    source_reference: str
    required_content: dict[str, str]
    visual_direction: str
    spatial_direction: str
    text_direction: str
    colour_direction: str
    emotional_direction: str
    production_constraints: list[str]
    preservation_requirements: list[str]
    channel: str
    width: int
    height: int


@dataclass(frozen=True)
class LayoutBox:
    left: int
    top: int
    right: int
    bottom: int


def ask(
    label: str,
    default: str = "",
    allow_empty: bool = False,
    required_message: str = "A value is required to keep the workflow defined.",
) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"{label}{suffix}: ").strip() or default
        if value or allow_empty:
            return value
        print(required_message)


def is_russian_text(value: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", value))


def is_missing(value: str) -> bool:
    return not value.strip()


def infer_topic(value: str) -> str:
    normalized = value.strip().lower()
    if "остеопор" in normalized:
        return "остеопороз"
    if "кальц" in normalized:
        return "кальций"
    if "сустав" in normalized or "joint" in normalized:
        return "суставы" if is_russian_text(value) else "joints"
    return ""


def topic_family(topic: str) -> str:
    normalized_topic = infer_topic(topic) or topic
    if normalized_topic in {"кальций", "остеопороз"}:
        return "bone_health"
    if normalized_topic in {"суставы", "joints"}:
        return "joint_health"
    return normalized_topic


def parse_product_input(value: str, request: str) -> tuple[str | None, str | None]:
    candidate = value.strip()
    normalized = candidate.lower()
    topic = infer_topic(candidate) or None
    command = re.search(
        r"\b(сделай|создай|подготовь|разработай|нарисуй|make|create|design)\b.*\b(постер|баннер|креатив|изображение|poster|banner|image)\b",
        normalized,
    )
    topic_only = normalized in {
        "кальций", "кальция", "суставы", "суставов", "остеопороз",
        "профилактика суставов", "профилактика остеопороза",
        "joint prevention", "joints", "calcium", "osteoporosis prevention",
    }
    generic_offer = re.fullmatch(
        r"(продукт|услуга|product|service)(\s+(для|for)\s+.+)?",
        normalized,
    )
    if not candidate or command or topic_only or generic_offer or normalized == request.strip().lower():
        return None, topic
    return candidate, topic


def is_generic_product(value: str, request: str) -> bool:
    product, _ = parse_product_input(value, request)
    return product is None


def is_generic_audience(value: str) -> bool:
    return value.strip().lower() in {"", "general audience", "общая аудитория", "все"}


def _clean_extracted_value(value: str) -> str:
    return value.strip().strip(" \t\r\n.,;:—–-")


def _extract_labeled_value(request: str, labels: str) -> str:
    quote_pairs = (("«", "»"), ('"', '"'), ("“", "”"))
    prefix = rf"(?i)(?<!\w)(?:{labels})\s*(?:[:—–-]\s*)?"
    for opening, closing in quote_pairs:
        match = re.search(prefix + re.escape(opening) + rf"(?P<value>[^{re.escape(closing)}]+)" + re.escape(closing), request)
        if match:
            return _clean_extracted_value(match.group("value"))
    match = re.search(prefix + r"(?P<value>[^.!?;\r\n]+)", request)
    return _clean_extracted_value(match.group("value")) if match else ""


def infer_brand(request: str, product: str = "") -> str:
    explicit = _extract_labeled_value(request, r"бренд|brand")
    if explicit:
        return explicit
    known = re.search(r"\bFOHOW\b", request, flags=re.IGNORECASE)
    if known:
        return known.group(0).upper()
    candidates = re.findall(r"(?<!\w)[A-ZА-ЯЁ][A-ZА-ЯЁ0-9_-]{1,}(?!\w)", product or request)
    excluded = {"CTA", "SVG", "JSON", "TXT", "RGB", "CMYK"}
    return next((candidate for candidate in reversed(candidates) if candidate not in excluded), "")


def infer_asset_type(request: str) -> str:
    value = request.lower()
    if "9:16" in value or ("whatsapp" in value and "статус" in value):
        return "Статус WhatsApp 9:16" if is_russian_text(request) else "WhatsApp status 9:16"
    if "1:1" in value or "1080x1080" in value or "1080×1080" in value or "квадрат" in value or "square" in value:
        return "Квадрат 1:1 — 1080×1080" if is_russian_text(request) else "Square social image 1:1"
    if "1200x628" in value or "1200×628" in value or "горизонт" in value or "landscape" in value:
        return "Горизонтальный — 1200×628" if is_russian_text(request) else "Landscape social image"
    if "постер" in value or "poster" in value:
        return "Постер" if is_russian_text(request) else "Poster"
    return "Цифровой материал" if is_russian_text(request) else "Digital Asset"


def parse_format(value: str) -> tuple[str, str, int, int] | None:
    normalized = value.strip().lower().replace("×", "x")
    if "whatsapp" in normalized or "9:16" in normalized or "1080x1920" in normalized:
        return "WhatsApp Status", "WhatsApp Status 9:16", 1080, 1920
    if "square" in normalized or "квадрат" in normalized or "1:1" in normalized or "1080x1080" in normalized:
        return "Social media", "Square social image 1:1", 1080, 1080
    if "landscape" in normalized or "горизонт" in normalized or "1200x628" in normalized:
        return "Social media", "Landscape social image", 1200, 628
    return None


def format_is_complete(context: ProjectContext) -> bool:
    generic_types = {"", "poster", "постер", "digital asset", "цифровой материал"}
    return (
        bool(context.channel.strip())
        and context.asset_type.strip().lower() not in generic_types
        and context.width > 0
        and context.height > 0
    )


def professional_display_cta(expected_action: str) -> str:
    value = expected_action.strip()
    normalized = value.lower()
    if not value:
        return ""
    if "whatsapp" in normalized:
        if any(word in normalized for word in ("напиши", "напишите", "написать", "write")):
            return "Напишите в WhatsApp" if is_russian_text(value) else "Message us on WhatsApp"
        return "Подробнее в WhatsApp" if is_russian_text(value) else "Learn more on WhatsApp"
    if any(word in normalized for word in ("смотри", "посмотри", "смотрите")):
        return "Узнайте подробнее"
    return value


def normalize_expected_action(display_cta: str) -> str:
    value = _clean_extracted_value(display_cta)
    if not value:
        return ""
    normalized = value.lower()
    replacements = (
        (r"^(?:пожалуйста,?\s*)?напиш(?:ите|и)\s+(?:нам\s+|мне\s+)?", "написать "),
        (r"^свяжитесь\s+(?:с\s+нами\s*)?", "связаться "),
        (r"^позвоните\s+(?:нам\s*)?", "позвонить "),
        (r"^запишитесь\s+", "записаться "),
        (r"^закажите\s+", "заказать "),
        (r"^купите\s+", "купить "),
        (r"^узнайте\s+", "узнать "),
        (r"^перейдите\s+", "перейти "),
        (r"^оставьте\s+", "оставить "),
    )
    for pattern, replacement in replacements:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            value = re.sub(pattern, replacement, value, count=1, flags=re.IGNORECASE)
            break
    value = re.sub(r"\s+", " ", value).strip()
    if "whatsapp" in value.lower():
        value = re.sub(r"whatsapp", "WhatsApp", value, flags=re.IGNORECASE)
    return value[:1].lower() + value[1:] if value else ""


def parse_natural_request(request: str) -> ParsedRequest:
    product = _extract_labeled_value(request, r"(?:о\s+)?продукт(?:е|а|ом)?|product")
    brand = infer_brand(request, product)
    if product and brand and product.casefold() == brand.casefold():
        product = ""
    elif product:
        parsed_product, _ = parse_product_input(product, request)
        product = parsed_product or ""

    audience = _extract_labeled_value(request, r"аудитория|целевая\s+аудитория|audience")
    if not audience:
        audience_match = re.search(
            r"(?i)(?<!\w)для\s+(?P<value>(?:мужчин(?:\s+и\s+женщин)?|женщин(?:\s+и\s+мужчин)?|людей|взрослых|родителей|предпринимателей|специалистов)[^.!?;\r\n]*?)(?=\s+(?:нужен|нужна|нужно|требуется)\b|[.!?;\r\n]|$)",
            request,
        )
        audience = _clean_extracted_value(audience_match.group("value")) if audience_match else ""

    explicit_topic = _extract_labeled_value(request, r"тема|тематика|topic")
    topic = explicit_topic or infer_topic(request)

    display_cta = _extract_labeled_value(request, r"призыв|cta")
    action_value = _extract_labeled_value(request, r"действие|action")
    expected_action = normalize_expected_action(display_cta or action_value)
    if not display_cta and action_value:
        display_cta = professional_display_cta(expected_action)

    return ParsedRequest(
        brand=brand,
        product=product,
        audience=audience,
        topic=topic,
        expected_action=expected_action,
        display_cta=display_cta,
        asset_type=infer_asset_type(request),
    )


def infer_objective(request: str) -> str:
    value = request.lower()
    russian = is_russian_text(request)
    if any(word in value for word in ("продаж", "купи", "закаж", "sale", "buy")):
        return "Ясно представить предложение и побудить к коммерческому отклику" if russian else "Present the offer clearly and encourage a commercial response"
    if any(word in value for word in ("профилакти", "объясн", "информ", "educat")):
        return "Объяснить ценность профилактики и предложить осознанный следующий шаг" if russian else "Explain the value of prevention and encourage an informed next action"
    return "Ясно передать предложение и предложить уместный следующий шаг" if russian else "Communicate the offer clearly and encourage a relevant next action"


def audience_need(audience: str, objective: str) -> str:
    value = f"{audience} {objective}".lower()
    russian = is_russian_text(f"{audience} {objective}")
    if any(word in value for word in ("50+", "55+", "60+", "пожил", "старш")):
        return "Сохранять подвижность, самостоятельность и уверенность без запугивания" if russian else "Maintain mobility, independence and confidence without fear-based communication"
    return "Быстро понять практическую ценность и увидеть убедительный следующий шаг" if russian else "Understand the practical value quickly and see a credible next step"


def meaningful_hero(audience: str, product: str) -> str:
    value = audience.lower()
    russian = is_russian_text(f"{audience} {product}")
    if any(word in value for word in ("50+", "55+", "60+", "пожил", "старш")):
        return "активный взрослый человек примерно 55–70 лет, достоверный и узнаваемый для аудитории" if russian else "active adult aged approximately 55–70, visibly credible for the audience"
    if is_generic_audience(audience):
        return f"человек, чей возраст и жизненную ситуацию необходимо уточнить для продукта «{product}»" if russian else f"person whose age and situation must be clarified for {product}"
    return f"человек, достоверно представляющий аудиторию «{audience}»" if russian else f"person visibly representative of {audience}"


def emotional_direction(objective: str) -> str:
    value = objective.lower()
    russian = is_russian_text(objective)
    if any(word in value for word in ("sale", "buy", "launch", "offer", "продаж", "акци", "запуск")):
        return "уверенное, релевантное и умеренно срочное" if russian else "confident, relevant and proportionately urgent"
    if any(word in value for word in ("trust", "health", "care", "prevent", "довер", "здоров", "забот", "профилакти")):
        return "спокойное, поддерживающее и вызывающее доверие" if russian else "calm, reassuring and trustworthy"
    return "ясное, уверенное и релевантное" if russian else "clear, confident and relevant"


def color_strategy(emotion: str) -> tuple[str, str, str]:
    if "urgent" in emotion or "сроч" in emotion:
        return "#17121F", "#FF7A45", "#FFF8F3"
    if "calm" in emotion or "спокой" in emotion:
        return "#082B3C", "#FF7657", "#F7FBFA"
    return "#10213B", "#79C7FF", "#F6FAFF"


def core_message(context: ProjectContext) -> str:
    topic = infer_topic(context.topic) or context.topic or infer_topic(context.request)
    if topic == "суставы" or topic == "joints":
        return "Забота о суставах — часть активной жизни"
    if topic == "кальций":
        return "Кальций — часть ежедневной заботы о здоровье костей"
    if topic == "остеопороз":
        return "Профилактика остеопороза начинается с осознанной заботы о здоровье костей"
    return context.product


def product_message(context: ProjectContext, product: str) -> str:
    if re.search(r"[А-Яа-яЁё]", context.request):
        return f"{product} — конкретный подход к ежедневной профилактике"
    return f"{product}: a concrete role in daily prevention"


class CreativeEngine:
    """CIM implementation: understands, exposes gaps, recommends and decides."""

    def __init__(self, context: ProjectContext) -> None:
        self.context = context
        parsed_format = parse_format(context.asset_type)
        if parsed_format:
            channel, asset_type, width, height = parsed_format
            self.context.channel = self.context.channel or channel
            self.context.asset_type = asset_type
            self.context.width = self.context.width or width
            self.context.height = self.context.height or height
        if not self.context.display_cta:
            self.context.display_cta = professional_display_cta(self.context.expected_action)
        self.semantic_model = self._build_semantic_model()
        self.knowledge_gaps = self._find_knowledge_gaps()
        self.directions: list[CreativeDirection] = []
        self.selected_direction_id: str | None = None
        self.decisions: dict[str, Decision] = {}
        if not self.blocking_gaps():
            self._start_creative_reasoning()

    @property
    def russian(self) -> bool:
        return is_russian_text(self.context.request)

    def _start_creative_reasoning(self, revised: bool = False) -> None:
        self.directions = self._build_directions()
        self.selected_direction_id = self.recommended_direction_id()
        self.decisions = self._build_decisions(revised=revised)

    def _build_semantic_model(self) -> SemanticModel:
        context = self.context
        russian = self.russian
        facts = context.research if context.research != NO_RESEARCH else ("Только контекст, предоставленный пользователем" if russian else "User-supplied context only")
        return SemanticModel(
            brand=context.brand or ("Бренд не определён" if russian else "Unknown brand"),
            offer=context.product or ("Конкретный продукт или услуга не определены" if russian else "Concrete product or service not identified"),
            topic=context.topic or infer_topic(context.request) or ("Тема не определена" if russian else "Topic not identified"),
            audience=context.audience or ("Аудитория не определена" if russian else "Audience not identified"),
            objective=context.objective,
            expected_action=context.expected_action or ("Следующее действие не определено" if russian else "Next action not identified"),
            audience_need=audience_need(context.audience, context.objective),
            trust_basis=context.trust_evidence or ("Утверждённые основания доверия не предоставлены" if russian else "No approved trust evidence supplied"),
            factual_basis=facts,
        )

    def _find_knowledge_gaps(self) -> list[KnowledgeGap]:
        context = self.context
        russian = self.russian
        gaps: list[KnowledgeGap] = []
        if is_missing(context.brand):
            gaps.append(KnowledgeGap("brand", "Какому бренду принадлежит эта коммуникация?" if russian else "Which brand owns this communication?", "Идентичность бренда определяет границы сообщения и визуального языка." if russian else "Brand identity constrains the message and visual language.", True))
        if is_generic_product(context.product, context.request):
            gaps.append(KnowledgeGap("product", "Какой конкретный продукт или услуга продвигается?" if russian else "What concrete product or service is being promoted?", "Тема не является коммерческим предложением; VisualMind не должен придумывать продукт FOHOW." if russian else "A topic is not a commercial offer; VisualMind must not invent a FOHOW product.", True))
        elif context.product.strip().casefold() == context.brand.strip().casefold():
            gaps.append(KnowledgeGap("product", "Каково точное название продукта, отличное от названия бренда?" if russian else "What is the exact product name, distinct from the brand name?", "Название бренда не является названием конкретного продукта." if russian else "A brand name is not a concrete product name.", True))
        if is_generic_audience(context.audience):
            gaps.append(KnowledgeGap("audience", "Кто именно должен откликнуться на этот материал?" if russian else "Who specifically should respond to this asset?", "Визуальный герой, язык и читаемость зависят от реальной аудитории." if russian else "Hero, language and readability depend on the real audience.", True))
        if is_missing(context.expected_action):
            gaps.append(KnowledgeGap("expected_action", "Что должен сделать человек после просмотра материала?" if russian else "What should the viewer do after seeing the asset?", "Маркетинговому материалу необходимо явное следующее действие." if russian else "A marketing asset needs an explicit next action.", True))
        if not format_is_complete(context):
            gaps.append(KnowledgeGap("format", "Где будет опубликован материал и какой формат требуется?" if russian else "Where will the asset be published, and which format is required?", "Generator не должен самостоятельно выбирать канал или размеры изображения." if russian else "The Generator must not choose a channel or image dimensions autonomously.", True))
        if is_missing(context.trust_evidence):
            gaps.append(KnowledgeGap("trust_evidence", "Какие утверждённые факты могут сформировать доверие?" if russian else "Which approved facts may create trust?", "Коммуникация о здоровье не должна придумывать доказательства, эффекты продукта или заявления компании." if russian else "Health communication must not invent proof, product effects or company claims.", False))
        if context.research == NO_RESEARCH:
            gaps.append(KnowledgeGap("research", "Доступны ли утверждённое исследование или знания о бренде?" if russian else "Is approved research or brand knowledge available?", "Prototype 0.2.3 использует предоставленные исследования, но пока не получает их из интернета." if russian else "Prototype 0.2.3 can consume research but does not yet acquire it from the internet.", False))
        return gaps

    def blocking_gaps(self) -> list[KnowledgeGap]:
        return [gap for gap in self.knowledge_gaps if gap.blocking]

    def detected_topic_change(self, value: str) -> str | None:
        detected = infer_topic(value)
        current = self.context.topic or infer_topic(self.context.request)
        return detected if detected and detected != current else None

    def _build_directions(self) -> list[CreativeDirection]:
        context = self.context
        russian = self.russian
        hero = meaningful_hero(context.audience, context.product)
        emotion = emotional_direction(context.objective)
        product = context.product or ("продукт требует уточнения" if russian else "the product to be clarified")
        audience = context.audience or ("аудитория требует уточнения" if russian else "the audience to be clarified")
        return [
            CreativeDirection(
                "prevention",
                "Профилактика как активная жизнь" if russian else "Prevention as active living",
                core_message(context),
                hero,
                "Показать достоверную сцену повседневного движения: человек и ситуация объясняют ценность профилактики до появления выраженного дискомфорта." if russian else "Show a credible everyday movement scene; the person and situation explain why prevention matters before discomfort dominates life.",
                emotion,
                "Связывает профилактику с самостоятельностью и повседневной жизнью вместо абстрактного wellness-образа." if russian else "Connects prevention with independence and daily life instead of showing generic wellness imagery.",
                "Без конкретного продукта направление превращается только в социальное сообщение." if russian else "Without a concrete product, this becomes only a social message.",
            ),
            CreativeDirection(
                "product",
                "Объяснение через продукт" if russian else "Product-led explanation",
                product_message(context, product),
                f"продукт «{product}» как главный визуальный объект, дополненный одной значимой для аудитории человеческой деталью" if russian else f"{product} as the primary focal object, supported by one audience-relevant human detail",
                "Однозначно показать реальный продукт и его утверждённую роль; использовать только предоставленные заявления и исходные материалы." if russian else "Make the real product and its approved role unmistakable; use only supplied claims and source materials.",
                "ясное, фактическое и вызывающее доверие" if russian else "clear, factual and trustworthy",
                "Подходит, когда коммерческий приоритет — узнаваемость конкретного продукта и его подтверждённой ценности." if russian else "Best when recognition of a specific product and its legitimate value is the commercial priority.",
                "Направление слабо или небезопасно без данных о продукте, упаковки или утверждённых заявлений." if russian else "Weak or unsafe if product data, packaging or approved claims are unavailable.",
            ),
            CreativeDirection(
                "trust",
                "Сначала доверие, затем предложение" if russian else "Trust before offer",
                "Доверие начинается с проверенных фактов" if re.search(r"[А-Яа-яЁё]", context.request) else "A credible reason to consider prevention",
                f"достоверный эксперт или консультант, релевантный аудитории «{audience}», только если его роль подтверждена фактами" if russian else f"a credible guide or practitioner relevant to {audience}, only when that role is factually supported",
                "Начать с утверждённых доказательств, происхождения или экспертизы; оставить продукт вторичным до формирования доверия." if russian else "Lead with approved evidence, origin or expertise; keep the product secondary until trust is established.",
                "авторитетное, спокойное и уважительное" if russian else "authoritative, calm and respectful",
                "Полезно для скептически настроенной аудитории, когда проверенные доказательства сильнее прямого продуктового обещания." if russian else "Useful for sceptical audiences when verified evidence is stronger than a direct product promise.",
                "Нельзя подразумевать медицинский авторитет, традицию или результаты, не подтверждённые исследованием." if russian else "Must not imply medical authority, tradition or results that the research does not establish.",
            ),
        ]

    def recommended_direction_id(self) -> str:
        if self.context.trust_evidence and not is_generic_product(self.context.product, self.context.request):
            return "product"
        return "prevention"

    @property
    def selected_direction(self) -> CreativeDirection:
        if self.selected_direction_id is None or self.blocking_gaps():
            raise WorkflowBlocked(self.blocked_reasoning_message())
        return next(item for item in self.directions if item.direction_id == self.selected_direction_id)

    def interpret_direction_selection(self, value: str) -> tuple[str, str | None]:
        normalized = value.strip().lower()
        if not normalized:
            return self.recommended_direction_id(), None
        aliases = {
            "1": "prevention",
            "2": "product",
            "3": "trust",
            "prevention": "prevention",
            "профилактика": "prevention",
            "product": "product",
            "продукт": "product",
            "trust": "trust",
            "доверие": "trust",
        }
        direction_id = aliases.get(normalized)
        if direction_id is None:
            if any(word in normalized for word in ("профилакти", "предотвращ", "активная жизнь", "prevent")):
                direction_id = "prevention"
            elif any(word in normalized for word in ("довер", "эксперт", "факт", "trust", "evidence")):
                direction_id = "trust"
            elif any(word in normalized for word in ("продукт", "кальц", "товар", "product", "offer")):
                direction_id = "product"
        if direction_id is None:
            for item in self.directions:
                if normalized == item.name.lower():
                    direction_id = item.direction_id
                    break
        if direction_id is None:
            message = "Не удалось понять выбор направления. Введите Enter, номер, название или опишите желаемый смысл." if self.russian else "The direction was not understood. Press Enter, enter a number or name, or describe the intended meaning."
            raise ValueError(message)
        return direction_id, self.detected_topic_change(value)

    def select_direction(self, direction_id: str) -> None:
        if self.blocking_gaps():
            raise WorkflowBlocked(self.blocked_reasoning_message())
        direction_id, _ = self.interpret_direction_selection(direction_id)
        self.selected_direction_id = direction_id
        self.decisions = self._build_decisions(revised=True)

    def _decision(self, key: str, area: str, statement: str, rationale: str, sources: list[str], risks: list[str] | None = None, revised: bool = False) -> Decision:
        russian = self.russian
        return Decision(
            decision_id=key,
            area=area,
            statement=statement,
            rationale=rationale,
            source_references=sources,
            constraints=[f"Должно поддерживать цель: {self.context.objective}" if russian else f"Must support the objective: {self.context.objective}", "Нельзя добавлять неподтверждённые заявления о здоровье или продукте." if russian else "Must not introduce unverified health or product claims."],
            assumptions=["Контекст, предоставленный пользователем, актуален и точен." if russian else "User-supplied context is current and accurate."],
            risks=risks or (["Реакция аудитории является обоснованным ожиданием, а не гарантией."] if russian else ["Audience response is an informed expectation, not a guarantee."]),
            state=DecisionState.REVISED if revised else DecisionState.DRAFT,
            user_confirmation="Not confirmed after revision" if revised else "Not confirmed",
        )

    def _build_decisions(self, revised: bool = False) -> dict[str, Decision]:
        context = self.context
        russian = self.russian
        direction = self.selected_direction
        emotion = direction.emotional_strategy
        evidence = context.trust_evidence or ("Не использовать неподтверждённые заявления о доверии или эффективности." if russian else "Use no unsupported trust or effectiveness claim.")
        return {
            "communication": self._decision("communication", "Коммуникационная стратегия" if russian else "Communication Strategy", direction.name, direction.rationale, ["Semantic Model", "Creative Context", "Structured Research Result"], [direction.risk], revised),
            "message": self._decision("message", "Основное сообщение" if russian else "Core Message", direction.core_idea, f"Выражает выбранную стратегию для аудитории «{context.audience}», не повторяя команду пользователя." if russian else f"Expresses the selected strategy for {context.audience} without repeating the user's command.", ["User Request", "Semantic Model"], revised=revised),
            "trust": self._decision("trust", "Стратегия доверия" if russian else "Trust Strategy", evidence, "Отделяет утверждённые доказательства от предположений и предотвращает вымышленные заявления о здоровье." if russian else "Separates approved evidence from assumptions and prevents invented health claims.", ["Structured Research Result", "User-supplied evidence"], revised=revised),
            "emotion": self._decision("emotion", "Эмоциональная стратегия" if russian else "Emotional Strategy", emotion, f"Поддерживает цель «{context.objective}» и потребность аудитории: {self.semantic_model.audience_need}." if russian else f"Supports {context.objective} and the audience need: {self.semantic_model.audience_need}.", ["EMOTIONAL_DESIGN.md", "HUMAN_PERCEPTION.md"], revised=revised),
            "visual": self._decision("visual", "Визуальная стратегия" if russian else "Visual Strategy", f"{direction.hero}. {direction.visual_strategy}", "Визуальный герой выполняет смысловую роль и не используется как случайное украшение." if russian else "The visual hero has a semantic role and is not selected as generic decoration.", ["COMPOSITION.md", "GESTALT.md", "PERCEPTION_MODEL.md", "Semantic Model"], [direction.risk], revised),
            "hierarchy": self._decision("hierarchy", "Информационная иерархия" if russian else "Information Hierarchy", "Бренд -> основное сообщение -> конкретный продукт или ценность -> утверждённое основание доверия -> призыв к действию." if russian else "Brand -> core message -> concrete product or value -> approved trust cue -> call to action.", "Ведёт от узнавания и смысла к доказательству и действию с контролируемой когнитивной нагрузкой." if russian else "Moves from recognition and meaning to proof and action with controlled cognitive load.", ["COMPOSITION.md", "TYPOGRAPHY.md", "HUMAN_PERCEPTION.md"], revised=revised),
            "action": self._decision("action", "Ожидаемое действие" if russian else "Expected Action", context.expected_action or ("Не определено" if russian else "Not defined"), "Делает ожидаемую реакцию аудитории явной и измеримой." if russian else "Makes the expected audience response explicit and measurable.", ["Creative Context", "Semantic Model"], revised=revised),
            "display_cta": self._decision("display_cta", "Текст CTA на макете" if russian else "Display CTA", context.display_cta, "Преобразует намерение пользователя в профессиональную финальную формулировку, которую пользователь подтверждает до производства." if russian else "Turns the user's intended action into professional final copy confirmed before production.", ["Expected Action", "User Confirmation"], revised=revised),
            "colour": self._decision("colour", "Цветовая стратегия" if russian else "Colour Strategy", f"Использовать согласованную палитру, поддерживающую направление «{emotion}» и утверждённый контекст бренда {context.brand}." if russian else f"Use a coherent palette supporting a {emotion} direction and the approved {context.brand or 'brand'} context.", "Цвет поддерживает внимание и эмоциональную согласованность, но не заменяет знания о бренде." if russian else "Colour supports attention and emotional consistency; it is not a substitute for brand knowledge.", ["COLOR_PSYCHOLOGY.md", "EMOTIONAL_DESIGN.md"], revised=revised),
        }

    def recalculate(self, changed_field: str, value: str) -> None:
        editable = set(ProjectContext.__dataclass_fields__)
        if changed_field not in editable:
            raise ValueError(f"Unknown context field: {changed_field}")
        setattr(self.context, changed_field, value)
        if changed_field == "expected_action":
            self.context.display_cta = professional_display_cta(value)
            self.context.display_cta_confirmed = False
        elif changed_field == "display_cta":
            self.context.display_cta_confirmed = False
        if changed_field == "topic":
            product_topic = infer_topic(self.context.product)
            if product_topic and topic_family(product_topic) != topic_family(value):
                self.context.product = ""
        had_reasoning = bool(self.decisions)
        previous_direction = self.selected_direction_id
        self.semantic_model = self._build_semantic_model()
        self.knowledge_gaps = self._find_knowledge_gaps()
        if self.blocking_gaps():
            self.directions = []
            self.selected_direction_id = None
            self.decisions = {}
            return
        self.directions = self._build_directions()
        if not had_reasoning:
            self.selected_direction_id = self.recommended_direction_id()
            self.decisions = self._build_decisions()
            return
        available = {item.direction_id for item in self.directions}
        self.selected_direction_id = previous_direction if previous_direction in available else self.recommended_direction_id()
        affected: dict[str, set[str]] = {
            "request": {"communication", "message", "visual"},
            "topic": {"communication", "message", "emotion", "visual", "hierarchy", "colour"},
            "objective": {"communication", "message", "emotion", "visual", "hierarchy", "action", "colour"},
            "audience": {"communication", "message", "emotion", "visual", "hierarchy"},
            "brand": {"trust", "visual", "hierarchy", "colour"},
            "product": {"communication", "message", "trust", "visual", "hierarchy"},
            "asset_type": {"visual", "hierarchy"},
            "expected_action": {"hierarchy", "action", "display_cta"},
            "display_cta": {"display_cta"},
            "trust_evidence": {"communication", "trust", "visual", "hierarchy"},
            "research": {"communication", "trust", "emotion", "visual", "hierarchy", "colour"},
        }
        rebuilt = self._build_decisions(revised=True)
        for key in affected[changed_field]:
            self.decisions[key] = rebuilt[key]

    def understanding_summary(self) -> str:
        model = self.semantic_model
        russian = self.russian
        lines = [
            "\nПОНИМАНИЕ ЗАДАЧИ" if russian else "\nTASK UNDERSTANDING",
            f"Бренд: {model.brand}" if russian else f"Brand: {model.brand}",
            f"Предложение: {model.offer}" if russian else f"Offer: {model.offer}",
            f"Тема: {model.topic}" if russian else f"Topic: {model.topic}",
            f"Аудитория: {model.audience}" if russian else f"Audience: {model.audience}",
            f"Цель: {model.objective}" if russian else f"Objective: {model.objective}",
            f"Ожидаемое действие: {model.expected_action}" if russian else f"Expected action: {model.expected_action}",
            f"Потребность аудитории: {model.audience_need}" if russian else f"Audience need: {model.audience_need}",
        ]
        if self.knowledge_gaps:
            lines.append("Пробелы в знаниях:" if russian else "Knowledge gaps:")
            for gap in self.knowledge_gaps:
                level = ("БЛОКИРУЮЩИЙ" if gap.blocking else "ОТКРЫТЫЙ") if russian else ("BLOCKING" if gap.blocking else "OPEN")
                lines.append(f"- [{level}] {gap.question} — {gap.reason}")
        else:
            lines.append("Пробелы в знаниях: не обнаружены" if russian else "Knowledge gaps: none detected")
        return "\n".join(lines)

    def blocked_reasoning_message(self) -> str:
        if self.russian:
            fields = ", ".join(RU_FIELD_LABELS.get(gap.field, gap.field) for gap in self.blocking_gaps())
            return f"Творческое рассуждение остановлено. Сначала необходимо закрыть блокирующие пробелы: {fields}."
        fields = ", ".join(gap.field for gap in self.blocking_gaps())
        return f"Creative Reasoning is blocked until these knowledge gaps are resolved: {fields}."

    def directions_summary(self) -> str:
        if self.blocking_gaps() or not self.directions:
            raise WorkflowBlocked(self.blocked_reasoning_message())
        russian = self.russian
        lines = ["\nТВОРЧЕСКИЕ НАПРАВЛЕНИЯ" if russian else "\nCREATIVE DIRECTIONS"]
        recommended = self.recommended_direction_id()
        for index, item in enumerate(self.directions, start=1):
            marker = (" (РЕКОМЕНДУЕТСЯ)" if russian else " (RECOMMENDED)") if item.direction_id == recommended else ""
            display_id = RU_DIRECTION_IDS[item.direction_id] if russian else item.direction_id
            lines.extend([
                f"\n{index}. [{display_id}] {item.name}{marker}",
                f"  Идея: {item.core_idea}" if russian else f"  Idea: {item.core_idea}",
                f"  Визуальный герой: {item.hero}" if russian else f"  Visual hero: {item.hero}",
                f"  Обоснование: {item.rationale}" if russian else f"  Why: {item.rationale}",
                f"  Риск: {item.risk}" if russian else f"  Risk: {item.risk}",
            ])
        return "\n".join(lines)

    def creative_summary(self) -> str:
        if self.blocking_gaps() or not self.decisions:
            raise WorkflowBlocked(self.blocked_reasoning_message())
        russian = self.russian
        lines = [
            "\nТВОРЧЕСКОЕ РЕЗЮМЕ" if russian else "\nCREATIVE SUMMARY",
            f"Выбранное направление: {self.selected_direction.name}" if russian else f"Selected direction: {self.selected_direction.name}",
            f"Цель: {self.context.objective}" if russian else f"Objective: {self.context.objective}",
            f"Аудитория: {self.context.audience}" if russian else f"Audience: {self.context.audience}",
            f"Бренд / продукт: {self.context.brand} / {self.context.product}" if russian else f"Brand / Product: {self.context.brand} / {self.context.product}",
        ]
        for decision in self.decisions.values():
            lines.append(f"- {decision.area}: {decision.statement}")
        return "\n".join(lines)

    def confirm(self) -> StructuredResult:
        gaps = self.blocking_gaps()
        if gaps:
            raise WorkflowBlocked(self.blocked_reasoning_message())
        confirmation = "Подтверждено пользователем через Творческое резюме" if self.russian else "Confirmed by user through Creative Summary"
        self.context.display_cta_confirmed = True
        for decision in self.decisions.values():
            decision.state = DecisionState.CONFIRMED
            decision.user_confirmation = confirmation
        specification = CreativeSpecification(self.semantic_model, self.selected_direction, self.decisions)
        open_gaps = [gap for gap in self.knowledge_gaps if not gap.blocking]
        return StructuredResult(
            source="Creative Engine / CIM Prototype 0.2.3",
            purpose="Confirmed Creative Specification for production",
            content=specification,
            confidence="Medium" if open_gaps else "High",
            constraints=["Generator must not alter confirmed creative decisions.", "No unverified medical, product or company claim may be added."],
            assumptions=["User confirmation applies to the displayed Creative Summary."],
            risks=[gap.reason for gap in open_gaps] or ["Generated asset still requires evaluation against the confirmed direction."],
            metadata={"prototype": "0.2.3", "direction_id": self.selected_direction_id},
        )


def production_readiness_issues(result: StructuredResult, context: ProjectContext) -> list[str]:
    russian = is_russian_text(context.request)
    issues: list[str] = []
    product, _ = parse_product_input(context.product, context.request)
    if product is None:
        issues.append("не определено точное название продукта" if russian else "an exact product name is not defined")
    if context.product.strip() and context.product.strip().casefold() == context.brand.strip().casefold():
        issues.append("Product совпадает с Brand" if russian else "Product matches Brand")
    if is_generic_audience(context.audience):
        issues.append("не определена конкретная аудитория" if russian else "a specific audience is not defined")
    if not context.display_cta.strip():
        issues.append("не определён Display CTA" if russian else "Display CTA is not defined")
    if not context.display_cta_confirmed:
        issues.append("Display CTA не подтверждён пользователем" if russian else "Display CTA is not confirmed by the user")
    if not format_is_complete(context):
        issues.append("не определены канал, Asset Type и размеры" if russian else "channel, Asset Type and dimensions are not defined")
    elif (context.width, context.height) not in {(1080, 1920), (1080, 1080), (1200, 628)}:
        issues.append("размеры не поддерживаются Prototype 0.2.3" if russian else "dimensions are not supported by Prototype 0.2.3")
    gate_engine = CreativeEngine(context)
    if gate_engine.blocking_gaps():
        issues.append("остались блокирующие пробелы в знаниях" if russian else "blocking knowledge gaps remain")
    if not result.content.confirmed():
        issues.append("Creative Specification не подтверждена" if russian else "Creative Specification is not confirmed")
    return list(dict.fromkeys(issues))


def ensure_production_ready(result: StructuredResult, context: ProjectContext) -> None:
    issues = production_readiness_issues(result, context)
    if not issues:
        return
    if is_russian_text(context.request):
        details = "; ".join(issues)
        raise WorkflowBlocked(f"Production Readiness Gate не пройден: {details}.")
    raise WorkflowBlocked(f"Production Readiness Gate failed: {'; '.join(issues)}.")


def boxes_overlap(first: LayoutBox, second: LayoutBox) -> bool:
    return not (
        first.right <= second.left
        or second.right <= first.left
        or first.bottom <= second.top
        or second.bottom <= first.top
    )


def validate_svg_layout(width: int, height: int, boxes: dict[str, LayoutBox]) -> None:
    for name, box in boxes.items():
        if box.left < 0 or box.top < 0 or box.right > width or box.bottom > height:
            raise ValueError(
                f"SVG layout is outside the {width}x{height} viewBox: {name}={box}."
            )
        if box.left >= box.right or box.top >= box.bottom:
            raise ValueError(f"SVG layout contains an invalid box: {name}={box}.")
    for first, second in (("headline", "product"), ("product", "meta"), ("meta", "cta")):
        if boxes_overlap(boxes[first], boxes[second]):
            raise ValueError(f"SVG layout blocks overlap: {first} and {second}.")


def svg_layout(width: int, height: int, headline_line_count: int) -> tuple[dict[str, int], dict[str, LayoutBox]]:
    if (width, height) == (1080, 1920):
        metrics = {
            "left": 72, "hero_x": 790, "brand_y": 150, "brand_size": 34,
            "headline_y": 300, "headline_step": 100, "headline_size": 84,
            "product_y": 1450, "product_size": 48,
            "trust_y": 1540, "meta_size": 32,
            "cta_y": 1750, "cta_size": 38, "cta_height": 112, "cta_top_offset": 70,
            "hero_head_y": 830, "hero_curve_y": 920,
            "hero_bottom_y": 1320, "hero_hands_y": 1155, "wrap_width": 24,
            "max_headline_lines": 4,
        }
    elif (width, height) == (1080, 1080):
        metrics = {
            "left": 72, "hero_x": 820, "brand_y": 150, "brand_size": 32,
            "headline_y": 300, "headline_step": 94, "headline_size": 78,
            "product_y": 610, "product_size": 42,
            "trust_y": 690, "meta_size": 30,
            "cta_y": 930, "cta_size": 34, "cta_height": 100, "cta_top_offset": 62,
            "hero_head_y": 330, "hero_curve_y": 430,
            "hero_bottom_y": 790, "hero_hands_y": 680, "wrap_width": 13,
            "max_headline_lines": 3,
        }
    elif (width, height) == (1200, 628):
        metrics = {
            "left": 80, "hero_x": 1000, "brand_y": 130, "brand_size": 30,
            "headline_y": 190, "headline_step": 61, "headline_size": 60,
            "product_y": 430, "product_size": 36,
            "trust_y": 475, "meta_size": 26,
            "cta_y": 570, "cta_size": 32, "cta_height": 92, "cta_top_offset": 58,
            "hero_head_y": 185, "hero_curve_y": 190,
            "hero_bottom_y": 580, "hero_hands_y": 500, "wrap_width": 24,
            "max_headline_lines": 4,
        }
    else:
        raise ValueError(
            f"Unsupported production dimensions: {width}x{height}. "
            "Supported formats are 1080x1920, 1080x1080 and 1200x628."
        )
    line_count = max(1, min(headline_line_count, metrics["max_headline_lines"]))
    left = metrics["left"]
    hero_x = metrics["hero_x"]
    cta_width = min(width - 2 * left, 720)
    content_right = hero_x - 205 if width >= height else width - left
    boxes = {
        "brand": LayoutBox(left, metrics["brand_y"] - metrics["brand_size"], min(left + 430, width), metrics["brand_y"] + 8),
        "headline": LayoutBox(
            left,
            metrics["headline_y"] - metrics["headline_size"],
            content_right,
            metrics["headline_y"] + (line_count - 1) * metrics["headline_step"] + 12,
        ),
        "product": LayoutBox(left, metrics["product_y"] - metrics["product_size"], content_right, metrics["product_y"] + 10),
        "meta": LayoutBox(left, metrics["trust_y"] - metrics["meta_size"], content_right, metrics["trust_y"] + 8),
        "cta": LayoutBox(left, metrics["cta_y"] - metrics["cta_top_offset"], left + cta_width, metrics["cta_y"] - metrics["cta_top_offset"] + metrics["cta_height"]),
        "hero_head": LayoutBox(hero_x - 110, metrics["hero_head_y"] - 110, hero_x + 110, metrics["hero_head_y"] + 110),
        "hero_body": LayoutBox(hero_x - 186, metrics["hero_curve_y"] - 36, hero_x + 186, metrics["hero_bottom_y"] + 36),
    }
    validate_svg_layout(width, height, boxes)
    return metrics, boxes


def generation_specification(result: StructuredResult, context: ProjectContext) -> GenerationSpecification:
    ensure_production_ready(result, context)
    specification = result.content
    if not specification.confirmed():
        raise ValueError("A Generation Specification requires Confirmed Decisions.")
    decisions = specification.decisions
    background, accent, foreground = color_strategy(decisions["emotion"].statement)
    return GenerationSpecification(
        source_reference="Confirmed Creative Specification / Prototype 0.2.3",
        required_content={
            "brand": context.brand,
            "headline": decisions["message"].statement,
            "product": context.product,
            "trust_evidence": context.trust_evidence,
            "expected_action": decisions["action"].statement,
            "call_to_action": decisions["display_cta"].statement,
            "audience": context.audience,
        },
        visual_direction=decisions["visual"].statement,
        spatial_direction="One dominant hero zone and one readable information zone; preserve a clear path from message to action.",
        text_direction="Use a large headline, short supporting content and a distinct CTA; never print workflow instructions as advertising copy.",
        colour_direction=f"Background {background}; accent {accent}; foreground {foreground}; adapt only when approved brand evidence requires it.",
        emotional_direction=decisions["emotion"].statement,
        production_constraints=[f"Channel: {context.channel}", f"Asset type: {context.asset_type}", f"Dimensions: {context.width}x{context.height}", "Use only supplied product and trust facts.", "Keep text readable at phone size."],
        preservation_requirements=[decisions["communication"].statement, decisions["message"].statement, decisions["action"].statement, "Preserve the semantic role and audience relevance of the hero."],
        channel=context.channel,
        width=context.width,
        height=context.height,
    )


def generation_prompt(specification: GenerationSpecification, context: ProjectContext) -> str:
    content = specification.required_content
    trust = content["trust_evidence"] or "Утверждённые основания доверия не предоставлены."
    return "\n".join([
        "VISUALMIND — MODEL-AGNOSTIC GENERATION PROMPT",
        "",
        f"Задача: {context.request}",
        f"Бренд: {content['brand']}",
        f"Конкретный продукт: {content['product']}",
        f"Аудитория: {content['audience']}",
        f"Сообщение: {content['headline']}",
        f"Визуальный герой: {specification.visual_direction}",
        f"Композиция: {specification.spatial_direction}",
        f"Цветовая стратегия: {specification.colour_direction}",
        f"Формат: {context.asset_type}; {specification.width}x{specification.height}; канал: {specification.channel}",
        f"Display CTA: {content['call_to_action']}",
        "",
        "Обязательные элементы:",
        f"- бренд {content['brand']};",
        f"- продукт {content['product']};",
        f"- основное сообщение «{content['headline']}»;",
        f"- Display CTA «{content['call_to_action']}»;",
        f"- основание доверия: {trust}",
        "",
        "Ограничения и запреты:",
        "- не изменять подтверждённые творческие решения;",
        "- не добавлять неподтверждённые медицинские, продуктовые или корпоративные утверждения;",
        "- не превращать Expected Action или служебные инструкции в рекламный текст;",
        *[f"- {constraint}" for constraint in specification.production_constraints],
        *[f"- сохранить: {requirement}" for requirement in specification.preservation_requirements],
    ])


class LocalSvgGenerator:
    """Replaceable deterministic Generator implementation for Prototype 0.2.3."""

    def generate(
        self,
        specification: GenerationSpecification,
        output_dir: Path,
        asset_name: str,
        structured_result: StructuredResult | None = None,
    ) -> tuple[Path, Path]:
        content = specification.required_content
        background, accent, foreground = color_strategy(specification.emotional_direction)
        width, height = specification.width, specification.height
        metrics, _ = svg_layout(width, height, 1)
        headline_lines = textwrap.wrap(content["headline"], width=metrics["wrap_width"])[:metrics["max_headline_lines"]]
        metrics, _ = svg_layout(width, height, len(headline_lines))
        left = metrics["left"]
        hero_x = metrics["hero_x"]
        headline_y = metrics["headline_y"]
        headline_step = metrics["headline_step"]
        headline_size = metrics["headline_size"]
        brand_y = metrics["brand_y"]
        brand_size = metrics["brand_size"]
        product_y = metrics["product_y"]
        product_size = metrics["product_size"]
        trust_y = metrics["trust_y"]
        meta_size = metrics["meta_size"]
        cta_y = metrics["cta_y"]
        cta_size = metrics["cta_size"]
        cta_height = metrics["cta_height"]
        cta_top_offset = metrics["cta_top_offset"]
        hero_head_y = metrics["hero_head_y"]
        hero_curve_y = metrics["hero_curve_y"]
        hero_bottom_y = metrics["hero_bottom_y"]
        hero_hands_y = metrics["hero_hands_y"]
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", asset_name).strip("-") or "visualmind-asset"
        output_path = output_dir / f"{safe_name}.svg"
        trace_path = output_dir / f"{safe_name}.json"
        headline_svg = "".join(
            f'<text x="{left}" y="{headline_y + index * headline_step}" class="headline" '
            f'font-family="Segoe UI" font-size="{headline_size}" font-weight="700" '
            f'fill="{foreground}">{html.escape(line)}</text>'
            for index, line in enumerate(headline_lines)
        )
        trust = content["trust_evidence"] or "Без неподтверждённых обещаний"
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{background}"/>
      <stop offset="100%" stop-color="#07111D"/>
    </linearGradient>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#bg)"/>
  <circle cx="{hero_x}" cy="{hero_head_y}" r="110" fill="{accent}" opacity="0.26"/>
  <path d="M {hero_x - 150} {hero_bottom_y} Q {hero_x} {hero_curve_y} {hero_x + 150} {hero_bottom_y}" fill="none" stroke="{accent}" stroke-width="72" stroke-linecap="round" opacity="0.30"/>
  <circle cx="{hero_x - 105}" cy="{hero_hands_y}" r="20" fill="{accent}"/>
  <circle cx="{hero_x + 105}" cy="{hero_hands_y}" r="20" fill="{accent}"/>
  <rect x="{left}" y="82" width="126" height="8" rx="4" fill="{accent}"/>
  <text x="{left}" y="{brand_y}" class="brand" font-family="Segoe UI" font-size="{brand_size}" font-weight="700" letter-spacing="4" fill="{accent}">{html.escape(content['brand'].upper())}</text>
  {headline_svg}
  <text x="{left}" y="{product_y}" class="product" font-family="Segoe UI" font-size="{product_size}" font-weight="600" fill="{foreground}">{html.escape(content['product'])}</text>
  <text x="{left}" y="{trust_y}" class="meta" font-family="Segoe UI" font-size="{meta_size}" font-weight="400" fill="{foreground}" opacity="0.78">{html.escape(trust)}</text>
  <rect x="{left}" y="{cta_y - cta_top_offset}" width="{min(width - 2 * left, 720)}" height="{cta_height}" rx="{cta_height // 2}" fill="{accent}"/>
  <text x="{left + 34}" y="{cta_y}" class="cta" font-family="Segoe UI" font-size="{cta_size}" font-weight="700" fill="{background}">{html.escape(content['call_to_action'])}</text>
  <style>
    .brand {{ letter-spacing: 4px; }}
    .meta {{ opacity: .78; }}
  </style>
</svg>'''
        output_path.write_text(svg, encoding="utf-8")
        trace_payload = {
            "structured_result": asdict(structured_result) if structured_result else None,
            "generation_specification": asdict(specification),
        }
        trace_path.write_text(
            json.dumps(
                trace_payload,
                ensure_ascii=False,
                indent=2,
                default=lambda value: value.value if isinstance(value, Enum) else str(value),
            ),
            encoding="utf-8",
        )
        return output_path, trace_path


def build_context(args: argparse.Namespace) -> ProjectContext:
    request = args.request or ("" if args.auto_confirm else ask("User request"))
    if not request:
        raise WorkflowBlocked("--request is required for an automatic run.")
    parsed = parse_natural_request(request)
    expected_action = args.expected_action or parsed.expected_action
    return ProjectContext(
        request=request,
        objective=args.objective or infer_objective(request),
        audience=args.audience or parsed.audience,
        brand=args.brand or parsed.brand,
        product=args.product or parsed.product,
        asset_type=args.asset_type or parsed.asset_type,
        expected_action=expected_action,
        topic=parsed.topic,
        channel=args.channel or "",
        width=args.width or 0,
        height=args.height or 0,
        display_cta=args.display_cta or parsed.display_cta or professional_display_cta(expected_action),
        trust_evidence=args.trust_evidence or "",
        research=args.research or NO_RESEARCH,
    )


def confirm_topic_change(engine: CreativeEngine, new_topic: str) -> bool:
    current_topic = engine.context.topic or infer_topic(engine.context.request) or ("не определена" if engine.russian else "not identified")
    if engine.russian:
        print(f"\nОбнаружено изменение темы: «{current_topic}» -> «{new_topic}».")
        prompt = "Изменить тему проекта? [да/нет]: "
        yes, no = {"да", "д", "yes", "y"}, {"нет", "н", "no", "n"}
        retry = "Ответьте «да» или «нет»."
    else:
        print(f"\nTopic change detected: '{current_topic}' -> '{new_topic}'.")
        prompt = "Change the project topic? [yes/no]: "
        yes, no = {"yes", "y"}, {"no", "n"}
        retry = "Answer 'yes' or 'no'."
    while True:
        answer = input(prompt).strip().lower()
        if answer in yes:
            engine.recalculate("topic", new_topic)
            print(f"Тема проекта изменена: {new_topic}." if engine.russian else f"Project topic changed: {new_topic}.")
            return True
        if answer in no:
            print("Тема проекта сохранена без изменений." if engine.russian else "Project topic was not changed.")
            return False
        print(retry)


def apply_product_answer(engine: CreativeEngine, value: str) -> bool:
    product, detected_topic = parse_product_input(value, engine.context.request)
    topic_change = engine.detected_topic_change(value)
    if topic_change and not confirm_topic_change(engine, topic_change):
        print("Введите точное название продукта в рамках текущей темы." if engine.russian else "Enter an exact product name within the current topic.")
        return False
    if product is None:
        if engine.russian:
            topic_text = detected_topic or "указанная формулировка"
            print(f"«{topic_text}» распознано как тема, а не как точное название продукта. Укажите точное название продукта.")
        else:
            topic_text = detected_topic or "The supplied phrase"
            print(f"'{topic_text}' is a topic, not an exact product name. Enter the exact product name.")
        return False
    engine.recalculate("product", product)
    return True


def apply_format_answer(engine: CreativeEngine, value: str) -> bool:
    parsed = parse_format(value)
    if parsed is None:
        print("Укажите один из форматов: «WhatsApp Status 9:16» или «Landscape social image»." if engine.russian else "Enter one of the supported formats: 'WhatsApp Status 9:16' or 'Landscape social image'.")
        return False
    channel, asset_type, width, height = parsed
    engine.context.channel = channel
    engine.context.width = width
    engine.context.height = height
    engine.recalculate("asset_type", asset_type)
    return True


def resolve_blocking_gaps(engine: CreativeEngine, auto_confirm: bool) -> None:
    if auto_confirm:
        if engine.blocking_gaps():
            raise WorkflowBlocked(engine.blocked_reasoning_message())
        return
    labels = ({
        "brand": "Бренд",
        "product": "Конкретный продукт или услуга",
        "audience": "Целевая аудитория",
        "expected_action": "Ожидаемое действие зрителя",
        "display_cta": "Финальный текст CTA на макете",
        "format": "Канал и формат: WhatsApp Status 9:16 или Landscape social image",
    } if engine.russian else {
        "brand": "Brand",
        "product": "Concrete product or service",
        "audience": "Target audience",
        "expected_action": "Expected viewer action",
        "display_cta": "Final Display CTA copy",
        "format": "Channel and format: WhatsApp Status 9:16 or Landscape social image",
    })
    required_message = "Значение обязательно: workflow не может перейти в неопределённое состояние." if engine.russian else "A value is required to keep the workflow defined."
    while engine.blocking_gaps():
        gap = engine.blocking_gaps()[0]
        value = ask(labels[gap.field], required_message=required_message)
        if gap.field == "product":
            apply_product_answer(engine, value)
            continue
        if gap.field == "format":
            apply_format_answer(engine, value)
            continue
        engine.recalculate(gap.field, value)


def choose_direction(engine: CreativeEngine, auto_confirm: bool, requested: str | None) -> None:
    if requested:
        try:
            direction_id, topic_change = engine.interpret_direction_selection(requested)
        except ValueError as error:
            if auto_confirm:
                raise WorkflowBlocked(str(error)) from error
            print(error)
        else:
            if topic_change:
                if auto_confirm:
                    raise WorkflowBlocked("Изменение темы требует явного подтверждения пользователя." if engine.russian else "A topic change requires explicit user confirmation.")
                if confirm_topic_change(engine, topic_change) and engine.blocking_gaps():
                    resolve_blocking_gaps(engine, auto_confirm=False)
            engine.select_direction(direction_id)
            return
        requested = None
    if auto_confirm:
        engine.select_direction(engine.recommended_direction_id())
        return
    print(engine.directions_summary())
    label = "Направление" if engine.russian else "Direction"
    message = "Необходимо выбрать направление." if engine.russian else "A direction is required."
    default = RU_DIRECTION_IDS[engine.recommended_direction_id()] if engine.russian else engine.recommended_direction_id()
    while True:
        answer = ask(label, default, required_message=message)
        try:
            direction_id, topic_change = engine.interpret_direction_selection(answer)
        except ValueError as error:
            print(error)
            continue
        if topic_change:
            if confirm_topic_change(engine, topic_change) and engine.blocking_gaps():
                resolve_blocking_gaps(engine, auto_confirm=False)
        engine.select_direction(direction_id)
        return


def confirm_with_user(engine: CreativeEngine, auto_confirm: bool) -> StructuredResult:
    if auto_confirm:
        print(engine.directions_summary())
        print(engine.creative_summary())
        print("\nПодтверждение передано автоматически." if engine.russian else "\nConfirmation supplied through --auto-confirm.")
        return engine.confirm()
    editable = ({
        "request": "Запрос пользователя",
        "objective": "Цель",
        "audience": "Аудитория",
        "brand": "Бренд",
        "product": "Конкретный продукт / услуга",
        "asset_type": "Тип цифрового материала",
        "expected_action": "Ожидаемое действие зрителя / CTA",
        "trust_evidence": "Утверждённые основания доверия",
        "research": "Сводка исследования",
    } if engine.russian else {
        "request": "User request",
        "objective": "Objective",
        "audience": "Audience",
        "brand": "Brand",
        "product": "Concrete product / service",
        "asset_type": "Digital Asset type",
        "expected_action": "Expected viewer action / CTA",
        "trust_evidence": "Approved trust evidence",
        "research": "Research summary",
    })
    required_message = "Значение обязательно: workflow не может перейти в неопределённое состояние." if engine.russian else "A value is required to keep the workflow defined."
    while True:
        print(engine.creative_summary())
        prompt = "\nВведите «подтвердить», «изменить» или «направление»: " if engine.russian else "\nType 'confirm', 'revise' or 'direction': "
        answer = input(prompt).strip().lower()
        if answer in {"confirm", "подтвердить"}:
            return engine.confirm()
        if answer in {"direction", "направление"}:
            print(engine.directions_summary())
            current = engine.selected_direction_id or engine.recommended_direction_id()
            default = RU_DIRECTION_IDS[current] if engine.russian else current
            while True:
                selection = ask("Направление" if engine.russian else "Direction", default, required_message=required_message)
                try:
                    direction_id, topic_change = engine.interpret_direction_selection(selection)
                except ValueError as error:
                    print(error)
                    continue
                if topic_change:
                    if confirm_topic_change(engine, topic_change) and engine.blocking_gaps():
                        resolve_blocking_gaps(engine, auto_confirm=False)
                engine.select_direction(direction_id)
                break
            continue
        if answer in {"revise", "изменить"}:
            print(("Поля: " + ", ".join(editable.values())) if engine.russian else ("Fields: " + ", ".join(editable)))
            field_input = ask("Поле для изменения" if engine.russian else "Field to revise", required_message=required_message)
            if engine.russian:
                reverse_fields = {label.lower(): key for key, label in editable.items()}
                field = reverse_fields.get(field_input.lower(), field_input)
            else:
                field = field_input
            if field not in editable:
                print("Неизвестное поле. Решения не изменены." if engine.russian else "Unknown field. No decision was changed.")
                continue
            value = ask(editable[field], allow_empty=field in {"trust_evidence", "research"}, required_message=required_message)
            if field == "product":
                apply_product_answer(engine, value)
            elif field == "asset_type":
                apply_format_answer(engine, value)
            else:
                engine.recalculate(field, value)
            resolve_blocking_gaps(engine, auto_confirm=False)
            continue
        print("Используйте только «подтвердить», «изменить» или «направление»." if engine.russian else "Use only 'confirm', 'revise' or 'direction'.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VisualMind Prototype 0.2.3")
    parser.add_argument("--request", help="Natural-language user request")
    parser.add_argument("--objective", help="Communication objective")
    parser.add_argument("--audience", help="Specific target audience")
    parser.add_argument("--brand", help="Brand")
    parser.add_argument("--product", help="Concrete product or service")
    parser.add_argument("--asset-type", help="Digital Asset type and format")
    parser.add_argument("--channel", help="Publication channel")
    parser.add_argument("--width", type=int, help="Output width in pixels")
    parser.add_argument("--height", type=int, help="Output height in pixels")
    parser.add_argument("--display-cta", help="Final CTA copy shown on the asset")
    parser.add_argument("--expected-action", help="Required viewer action / CTA")
    parser.add_argument("--trust-evidence", help="Approved trust facts or claims")
    parser.add_argument("--research", help="Optional Structured Research Result summary")
    parser.add_argument("--direction", help="Creative direction: ID, number, name or natural-language description")
    parser.add_argument("--output-dir", default="output", help="Output directory (default: output)")
    parser.add_argument("--asset-name", default="visualmind-asset", help="Generated SVG and JSON base name")
    parser.add_argument("--analysis-only", action="store_true", help="Print understanding, gaps and directions without production")
    parser.add_argument("--auto-confirm", action="store_true", help="Record explicit confirmation for a complete non-interactive run")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        context = build_context(args)
        engine = CreativeEngine(context)
        print(engine.understanding_summary())
        if args.analysis_only:
            if engine.blocking_gaps():
                print("\nТворческое рассуждение не начато: сначала закройте блокирующие пробелы." if engine.russian else "\nCreative Reasoning has not started: resolve blocking gaps first.")
                return 2
            print(engine.directions_summary())
            return 0
        resolve_blocking_gaps(engine, args.auto_confirm)
        choose_direction(engine, args.auto_confirm, args.direction)
        result = confirm_with_user(engine, args.auto_confirm)
        generation = generation_specification(result, context)
        asset, trace = LocalSvgGenerator().generate(generation, Path(args.output_dir), args.asset_name, result)
        if engine.russian:
            print(f"\nСоздан цифровой материал: {asset.resolve()}")
            print(f"Трассировка решений: {trace.resolve()}")
            print("Источник: подтверждённая творческая спецификация / прототип 0.2.3")
        else:
            print(f"\nGenerated Digital Asset: {asset.resolve()}")
            print(f"Decision trace: {trace.resolve()}")
            print("Source: Confirmed Creative Specification / Prototype 0.2.3")
        return 0
    except WorkflowBlocked as error:
        russian = 'context' in locals() and is_russian_text(context.request)
        print(f"\nРАБОЧИЙ ПРОЦЕСС ОСТАНОВЛЕН\n{error}" if russian else f"\nWORKFLOW BLOCKED\n{error}")
        print("Цифровой материал не создан." if russian else "No Digital Asset was generated.")
        return 2
    except ValueError as error:
        russian = 'context' in locals() and is_russian_text(context.request)
        print(f"\nНЕ УДАЛОСЬ ОБРАБОТАТЬ ОТВЕТ\n{error}" if russian else f"\nINPUT COULD NOT BE PROCESSED\n{error}")
        print("Исправьте ответ и повторите запуск." if russian else "Correct the input and run the command again.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
