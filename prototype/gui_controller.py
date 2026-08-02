"""State controller for VisualMind Studio GUI Prototype 0.3.

The controller coordinates existing VisualMind contracts. It contains no
creative reasoning and has no dependency on PySide6, so it can be tested
without opening a window.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from visualmind_prototype import (
    CreativeEngine,
    GenerationSpecification,
    LocalSvgGenerator,
    ProjectContext,
    WorkflowBlocked,
    format_is_complete,
    generation_prompt,
    generation_specification,
    infer_objective,
    parse_natural_request,
    parse_format,
)


FORMAT_OPTIONS = {
    "WhatsApp 9:16 — 1080×1920": "WhatsApp Status 9:16",
    "Квадрат 1:1 — 1080×1080": "Square social image 1:1",
    "Горизонтальный — 1200×628": "Landscape social image",
}

CONFIRMATION_KEYS = (
    "product",
    "audience",
    "display_cta",
    "format",
    "verified_facts",
    "direction",
)


@dataclass
class StudioState:
    request: str = ""
    request_dirty: bool = False
    context: ProjectContext | None = None
    engine: CreativeEngine | None = None
    confirmations: dict[str, bool] = field(
        default_factory=lambda: {key: False for key in CONFIRMATION_KEYS}
    )
    generated_asset: Path | None = None
    generated_trace: Path | None = None
    generated_prompt: Path | None = None
    prompt_text: str = ""
    generation_specification: GenerationSpecification | None = None


class StudioController:
    """Coordinates GUI state without owning Creative Engine decisions."""

    def __init__(self) -> None:
        self.state = StudioState()

    @property
    def engine(self) -> CreativeEngine | None:
        return self.state.engine

    @property
    def context(self) -> ProjectContext | None:
        return self.state.context

    def analyze(self, request: str) -> None:
        request = request.strip()
        if not request:
            raise ValueError("Опишите задачу перед анализом.")
        parsed = parse_natural_request(request)
        context = ProjectContext(
            request=request,
            objective=infer_objective(request),
            audience=parsed.audience,
            brand=parsed.brand,
            product=parsed.product,
            asset_type=parsed.asset_type,
            expected_action=parsed.expected_action,
            topic=parsed.topic,
            display_cta=parsed.display_cta,
        )
        self.state = StudioState(
            request=request,
            context=context,
            engine=CreativeEngine(context),
        )

    def fields(self) -> dict[str, str]:
        context = self.context
        if context is None:
            return {key: "" for key in ("brand", "topic", "product", "audience", "expected_action", "display_cta", "format")}
        format_label = next(
            (label for label, value in FORMAT_OPTIONS.items() if parse_format(value) == (context.channel, context.asset_type, context.width, context.height)),
            "",
        )
        return {
            "brand": context.brand,
            "topic": context.topic,
            "product": context.product,
            "audience": context.audience,
            "expected_action": context.expected_action,
            "display_cta": context.display_cta,
            "format": format_label,
        }

    def blocking_gap_fields(self) -> set[str]:
        if self.engine is None:
            return set()
        return {gap.field for gap in self.engine.blocking_gaps()}

    def knowledge_gaps(self) -> list[str]:
        if self.engine is None:
            return []
        return [
            f"{'БЛОКИРУЮЩИЙ' if gap.blocking else 'ОТКРЫТЫЙ'} · {gap.question}\n{gap.reason}"
            for gap in self.engine.knowledge_gaps
        ]

    def _reset_confirmation(self, *keys: str) -> None:
        for key in keys:
            self.state.confirmations[key] = False

    def invalidate_request(self, current_text: str) -> None:
        if self.engine is None:
            return
        self.state.request_dirty = current_text.strip() != self.state.request
        if self.state.request_dirty:
            self._reset_confirmation("direction")
            self.state.generated_asset = None
            self.state.generated_trace = None
            self.state.generated_prompt = None
            self.state.prompt_text = ""
            self.state.generation_specification = None

    def invalidate_field(self, field_name: str) -> None:
        dependencies = {
            "brand": ("product", "direction"),
            "theme": ("product", "direction"),
            "topic": ("product", "direction"),
            "product": ("product", "direction"),
            "audience": ("audience", "direction"),
            "expected_action": ("display_cta", "direction"),
            "final_cta": ("display_cta",),
            "display_cta": ("display_cta",),
            "trust_evidence": ("verified_facts", "direction"),
            "format": ("format", "direction"),
        }
        if field_name not in dependencies:
            raise ValueError(f"Неизвестное поле контекста: {field_name}")
        self._reset_confirmation(*dependencies[field_name])

    def update_field(self, field_name: str, value: str) -> None:
        if self.engine is None or self.context is None:
            raise WorkflowBlocked("Сначала выполните анализ задачи.")
        value = value.strip()
        if field_name == "format":
            parsed = parse_format(FORMAT_OPTIONS.get(value, value))
            if parsed is None:
                self.context.channel = ""
                self.context.width = 0
                self.context.height = 0
                self.engine.recalculate("asset_type", "Цифровой материал")
            else:
                channel, asset_type, width, height = parsed
                self.context.channel = channel
                self.context.width = width
                self.context.height = height
                self.engine.recalculate("asset_type", asset_type)
            self.invalidate_field("format")
        else:
            model_field = {"theme": "topic", "final_cta": "display_cta"}.get(field_name, field_name)
            if model_field not in {"brand", "topic", "product", "audience", "expected_action", "display_cta", "trust_evidence"}:
                raise ValueError(f"Неизвестное поле контекста: {field_name}")
            self.engine.recalculate(model_field, value)
            self.invalidate_field(model_field)
        self.state.generated_asset = None
        self.state.generated_trace = None
        self.state.generated_prompt = None
        self.state.prompt_text = ""
        self.state.generation_specification = None

    def select_direction(self, direction_id: str) -> None:
        if self.engine is None:
            raise WorkflowBlocked("Сначала выполните анализ задачи.")
        self.engine.select_direction(direction_id)
        self._reset_confirmation("direction")

    def set_confirmation(self, key: str, confirmed: bool) -> None:
        if key not in self.state.confirmations:
            raise ValueError(f"Неизвестное подтверждение: {key}")
        self.state.confirmations[key] = bool(confirmed)
        if key == "display_cta" and self.context is not None:
            self.context.display_cta_confirmed = bool(confirmed)

    def readiness_issues(self) -> list[str]:
        if self.engine is None or self.context is None:
            return ["Задача ещё не проанализирована."]
        issues = [gap.question for gap in self.engine.blocking_gaps()]
        if self.state.request_dirty:
            issues.append("Исходный запрос изменён и требует повторного анализа.")
        context = self.context
        if context.product and context.brand and context.product.casefold() == context.brand.casefold():
            issues.append("Продукт не может совпадать с брендом.")
        if not format_is_complete(context):
            issues.append("Не определены канал, формат и размеры.")
        if not context.display_cta.strip():
            issues.append("Не определён финальный призыв к действию.")
        confirmation_labels = {
            "product": "Продукт не подтверждён.",
            "audience": "Аудитория не подтверждена.",
            "display_cta": "Финальный призыв не подтверждён.",
            "format": "Формат не подтверждён.",
            "verified_facts": "Не подтверждено ограничение на использование только проверенных фактов.",
            "direction": "Творческое направление не подтверждено.",
        }
        for key, label in confirmation_labels.items():
            if not self.state.confirmations[key]:
                issues.append(label)
        if self.engine.selected_direction_id is None:
            issues.append("Творческое направление не выбрано.")
        return list(dict.fromkeys(issues))

    @property
    def can_generate(self) -> bool:
        return not self.readiness_issues()

    def creative_summary(self) -> str:
        if self.engine is None or self.engine.blocking_gaps():
            return "Творческое резюме появится после закрытия блокирующих пробелов."
        return self.engine.creative_summary().strip()

    def generation_preview(self) -> str:
        if self.engine is None or self.context is None or self.engine.blocking_gaps():
            return "Спецификация генерации пока недоступна."
        decisions = self.engine.decisions
        return "\n".join([
            f"Формат: {self.context.asset_type or 'не определён'}",
            f"Размер: {self.context.width}×{self.context.height}" if self.context.width else "Размер: не определён",
            f"Сообщение: {decisions['message'].statement}",
            f"Герой: {decisions['visual'].statement}",
            f"Цвет: {decisions['colour'].statement}",
            f"Финальный призыв: {decisions['display_cta'].statement}",
        ])

    def generate(self, output_dir: Path, asset_name: str = "visualmind-studio") -> tuple[Path, Path, Path]:
        issues = self.readiness_issues()
        if issues:
            raise WorkflowBlocked("Проверка готовности к производству не пройдена: " + "; ".join(issues))
        assert self.engine is not None and self.context is not None
        result = self.engine.confirm()
        specification = generation_specification(result, self.context)
        asset, trace = LocalSvgGenerator().generate(specification, output_dir, asset_name, result)
        prompt_text = generation_prompt(specification, self.context)
        prompt_path = output_dir / f"{asset.stem}.txt"
        prompt_path.write_text(prompt_text, encoding="utf-8")
        self.state.generated_asset = asset
        self.state.generated_trace = trace
        self.state.generated_prompt = prompt_path
        self.state.prompt_text = prompt_text
        self.state.generation_specification = specification
        return asset, trace, prompt_path

    def new_project(self) -> None:
        self.state = StudioState()
