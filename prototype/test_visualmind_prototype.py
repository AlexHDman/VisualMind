import io
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from visualmind_prototype import (
    CreativeEngine,
    LocalSvgGenerator,
    ProjectContext,
    WorkflowBlocked,
    boxes_overlap,
    choose_direction,
    generation_specification,
    main,
    parse_product_input,
    production_readiness_issues,
    svg_layout,
)


def complete_context(**changes: str) -> ProjectContext:
    values = {
        "request": "Сделай постер FOHOW о профилактике суставов",
        "objective": "Объяснить пользу профилактики и пригласить на консультацию",
        "audience": "Взрослые 50+",
        "brand": "FOHOW",
        "product": "Утверждённый продукт FOHOW для суставов",
        "asset_type": "WhatsApp status 9:16",
        "expected_action": "Напишите в WhatsApp",
        "trust_evidence": "Использовать только утверждённые сведения из каталога FOHOW",
        "research": "Утверждённая локальная сводка продукта",
    }
    values.update(changes)
    return ProjectContext(**values)


class CreativeEngineTests(unittest.TestCase):
    def test_product_equal_to_brand_blocks_production(self) -> None:
        context = complete_context(product="FOHOW")
        engine = CreativeEngine(context)
        self.assertIn("product", {gap.field for gap in engine.blocking_gaps()})
        with self.assertRaises(WorkflowBlocked):
            engine.confirm()
        ready_context = complete_context()
        ready_engine = CreativeEngine(ready_context)
        result = ready_engine.confirm()
        ready_context.product = "fohow"
        with self.assertRaises(WorkflowBlocked):
            generation_specification(result, ready_context)

    def test_command_is_not_accepted_as_product(self) -> None:
        product, topic = parse_product_input(
            "Сделай постер для кальция в Fohow",
            "Сделай постер FOHOW о профилактике суставов",
        )
        self.assertIsNone(product)
        self.assertEqual(topic, "кальций")

    def test_topic_is_not_accepted_as_concrete_product(self) -> None:
        for value, expected_topic in (
            ("кальций", "кальций"),
            ("профилактика остеопороза", "остеопороз"),
            ("суставы", "суставы"),
        ):
            with self.subTest(value=value):
                product, topic = parse_product_input(value, "Сделай постер FOHOW")
                self.assertIsNone(product)
                self.assertEqual(topic, expected_topic)

    def test_short_request_exposes_missing_marketing_knowledge(self) -> None:
        context = complete_context(
            product="Профилактика суставов",
            audience="",
            expected_action="",
            trust_evidence="",
            research="No additional research supplied.",
        )
        engine = CreativeEngine(context)
        fields = {gap.field for gap in engine.blocking_gaps()}
        self.assertEqual(fields, {"product", "audience", "expected_action"})
        self.assertEqual(engine.directions, [])
        self.assertEqual(engine.decisions, {})
        self.assertIsNone(engine.selected_direction_id)

    def test_blocking_gap_prevents_all_creative_reasoning_outputs(self) -> None:
        engine = CreativeEngine(complete_context(product="Суставы"))
        with self.assertRaises(WorkflowBlocked):
            engine.directions_summary()
        with self.assertRaises(WorkflowBlocked):
            engine.creative_summary()

    def test_reasoning_starts_only_after_last_blocking_gap_is_resolved(self) -> None:
        engine = CreativeEngine(complete_context(product="Суставы", audience="", expected_action=""))
        engine.recalculate("product", "Утверждённый продукт FOHOW для суставов")
        self.assertEqual(engine.directions, [])
        engine.recalculate("audience", "Взрослые 50+")
        self.assertEqual(engine.directions, [])
        engine.recalculate("expected_action", "Напишите в WhatsApp")
        self.assertEqual(len(engine.directions), 3)
        self.assertTrue(engine.decisions)

    def test_topic_change_recalculates_semantics_and_removes_old_joint_idea(self) -> None:
        engine = CreativeEngine(complete_context(product="FOHOW Кальций Комплекс"))
        self.assertEqual(engine.detected_topic_change("Сделай постер для кальция в Fohow"), "кальций")
        engine.recalculate("topic", "кальций")
        engine.select_direction("профилактика")
        self.assertEqual(engine.semantic_model.topic, "кальций")
        self.assertIn("Кальций", engine.decisions["message"].statement)
        self.assertNotIn("Забота о суставах", engine.decisions["message"].statement)

    def test_incompatible_product_is_cleared_after_topic_change(self) -> None:
        engine = CreativeEngine(complete_context())
        engine.recalculate("topic", "кальций")
        self.assertEqual(engine.context.product, "")
        self.assertIn("product", {gap.field for gap in engine.blocking_gaps()})
        self.assertEqual(engine.directions, [])

    def test_natural_language_direction_is_understood_as_prevention(self) -> None:
        engine = CreativeEngine(complete_context())
        direction_id, topic = engine.interpret_direction_selection("профилактика остеопороза")
        self.assertEqual(direction_id, "prevention")
        self.assertEqual(topic, "остеопороз")

    def test_unknown_direction_reprompts_without_traceback(self) -> None:
        engine = CreativeEngine(complete_context())
        output = io.StringIO()
        with patch("builtins.input", side_effect=["непонятный ответ", ""]), redirect_stdout(output):
            choose_direction(engine, auto_confirm=False, requested=None)
        self.assertEqual(engine.selected_direction_id, engine.recommended_direction_id())
        self.assertIn("Не удалось понять выбор направления", output.getvalue())

    def test_engine_refuses_confirmation_with_blocking_gap(self) -> None:
        engine = CreativeEngine(complete_context(product="Суставы"))
        with self.assertRaises(WorkflowBlocked):
            engine.confirm()

    def test_age_relevant_hero_is_semantic_not_generic(self) -> None:
        engine = CreativeEngine(complete_context())
        prevention = next(item for item in engine.directions if item.direction_id == "prevention")
        self.assertIn("55–70", prevention.hero)
        self.assertNotIn("young", prevention.hero.lower())
        self.assertIn("активный взрослый человек", prevention.hero)
        summary = engine.directions_summary()
        self.assertIn(f"Визуальный герой: {prevention.hero}", summary)
        self.assertNotIn("  Hero:", summary)

    def test_confirmed_spec_generates_vertical_asset_and_trace(self) -> None:
        context = complete_context()
        engine = CreativeEngine(context)
        engine.select_direction("product")
        with tempfile.TemporaryDirectory() as directory:
            result = engine.confirm()
            generation = generation_specification(result, context)
            asset, trace = LocalSvgGenerator().generate(generation, Path(directory), "fohow", result)
            asset_text = asset.read_text(encoding="utf-8")
            self.assertIn('width="1080" height="1920"', asset_text)
            self.assertIn("Напишите в WhatsApp", asset_text)
            self.assertIn('font-size="84"', asset_text)
            self.assertIn('font-size="48"', asset_text)
            self.assertIn('font-size="32"', asset_text)
            headline_lines = re.findall(r'class="headline"[^>]*>(.*?)</text>', asset_text)
            self.assertEqual(" ".join(headline_lines), engine.decisions["message"].statement)
            self.assertTrue(trace.exists())
            trace_text = trace.read_text(encoding="utf-8")
            self.assertIn('"source_reference"', trace_text)
            self.assertIn('"semantic_model"', trace_text)
            self.assertIn('"confidence"', trace_text)

    def test_missing_format_blocks_production(self) -> None:
        context = complete_context()
        engine = CreativeEngine(context)
        result = engine.confirm()
        context.channel = ""
        context.asset_type = "Постер"
        context.width = 0
        context.height = 0
        with self.assertRaises(WorkflowBlocked):
            generation_specification(result, context)

    def test_expected_action_is_separate_from_confirmed_display_cta(self) -> None:
        context = complete_context(expected_action="смотри whatsapp")
        engine = CreativeEngine(context)
        self.assertEqual(engine.decisions["action"].statement, "смотри whatsapp")
        self.assertEqual(engine.decisions["display_cta"].statement, "Подробнее в WhatsApp")
        summary = engine.creative_summary()
        self.assertIn("смотри whatsapp", summary)
        self.assertIn("Подробнее в WhatsApp", summary)
        result = engine.confirm()
        generation = generation_specification(result, context)
        self.assertEqual(generation.required_content["expected_action"], "смотри whatsapp")
        self.assertEqual(generation.required_content["call_to_action"], "Подробнее в WhatsApp")

    def test_whatsapp_status_has_explicit_1080_by_1920_dimensions(self) -> None:
        context = complete_context(asset_type="WhatsApp Status 9:16")
        engine = CreativeEngine(context)
        result = engine.confirm()
        generation = generation_specification(result, context)
        self.assertEqual((generation.width, generation.height), (1080, 1920))
        self.assertEqual(generation.channel, "WhatsApp Status")

    def test_landscape_social_image_has_explicit_1200_by_628_dimensions(self) -> None:
        context = complete_context(asset_type="Landscape social image")
        engine = CreativeEngine(context)
        result = engine.confirm()
        generation = generation_specification(result, context)
        self.assertEqual((generation.width, generation.height), (1200, 628))
        self.assertEqual(generation.channel, "Social media")

    def test_square_social_image_has_explicit_1080_by_1080_dimensions(self) -> None:
        context = complete_context(asset_type="Квадрат 1:1 — 1080×1080")
        engine = CreativeEngine(context)
        result = engine.confirm()
        generation = generation_specification(result, context)
        self.assertEqual((generation.width, generation.height), (1080, 1080))
        self.assertEqual(generation.channel, "Social media")

    def test_svg_meta_and_cta_do_not_overlap(self) -> None:
        _, boxes = svg_layout(1200, 628, 3)
        self.assertFalse(boxes_overlap(boxes["meta"], boxes["cta"]))

    def test_svg_typography_is_readable_in_vertical_and_landscape_formats(self) -> None:
        vertical, _ = svg_layout(1080, 1920, 3)
        landscape, _ = svg_layout(1200, 628, 3)
        self.assertGreaterEqual(vertical["headline_size"], 84)
        self.assertGreaterEqual(vertical["product_size"], 48)
        self.assertGreaterEqual(vertical["meta_size"], 32)
        self.assertGreaterEqual(vertical["cta_size"], 38)
        self.assertGreaterEqual(vertical["headline_step"], vertical["headline_size"])
        self.assertGreaterEqual(landscape["headline_size"], 60)
        self.assertGreaterEqual(landscape["product_size"], 36)
        self.assertGreaterEqual(landscape["meta_size"], 26)
        self.assertGreaterEqual(landscape["cta_size"], 32)
        self.assertGreaterEqual(landscape["headline_step"], landscape["headline_size"])

    def test_landscape_svg_uses_polished_typography_without_overflow(self) -> None:
        context = complete_context(asset_type="Landscape social image")
        engine = CreativeEngine(context)
        result = engine.confirm()
        generation = generation_specification(result, context)
        with tempfile.TemporaryDirectory() as directory:
            asset, _ = LocalSvgGenerator().generate(generation, Path(directory), "landscape", result)
            asset_text = asset.read_text(encoding="utf-8")
        self.assertIn('width="1200" height="628"', asset_text)
        self.assertIn('font-size="60"', asset_text)
        self.assertIn('font-size="36"', asset_text)
        self.assertIn('font-size="26"', asset_text)
        headline_lines = re.findall(r'class="headline"[^>]*>(.*?)</text>', asset_text)
        self.assertEqual(" ".join(headline_lines), engine.decisions["message"].statement)

    def test_svg_key_geometry_stays_inside_viewbox(self) -> None:
        for dimensions in ((1200, 628), (1080, 1080), (1080, 1920)):
            with self.subTest(dimensions=dimensions):
                width, height = dimensions
                _, boxes = svg_layout(width, height, 3)
                for name, box in boxes.items():
                    with self.subTest(name=name):
                        self.assertGreaterEqual(box.left, 0)
                        self.assertGreaterEqual(box.top, 0)
                        self.assertLessEqual(box.right, width)
                        self.assertLessEqual(box.bottom, height)

    def test_svg_is_not_saved_when_layout_validation_fails(self) -> None:
        context = complete_context()
        engine = CreativeEngine(context)
        result = engine.confirm()
        generation = generation_specification(result, context)
        generation.width = 500
        generation.height = 500
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            with self.assertRaises(ValueError):
                LocalSvgGenerator().generate(generation, output_dir, "invalid", result)
            self.assertEqual(list(output_dir.iterdir()), [])

    def test_generator_is_not_called_when_readiness_fails(self) -> None:
        arguments = [
            "visualmind_prototype.py",
            "--request", "Сделай постер FOHOW о профилактике суставов",
            "--objective", "Объяснить пользу профилактики",
            "--audience", "Взрослые 50+",
            "--brand", "FOHOW",
            "--product", "FOHOW",
            "--asset-type", "WhatsApp Status 9:16",
            "--expected-action", "Напишите в WhatsApp",
            "--auto-confirm",
        ]
        output = io.StringIO()
        with patch.object(sys, "argv", arguments), patch.object(LocalSvgGenerator, "generate") as generate, redirect_stdout(output):
            status = main()
        self.assertEqual(status, 2)
        generate.assert_not_called()

    def test_readiness_reports_unconfirmed_display_cta(self) -> None:
        context = complete_context()
        engine = CreativeEngine(context)
        result = engine.confirm()
        context.display_cta_confirmed = False
        issues = production_readiness_issues(result, context)
        self.assertIn("Display CTA не подтверждён пользователем", issues)

    def test_local_recalculation_marks_only_downstream_decisions(self) -> None:
        engine = CreativeEngine(complete_context())
        engine.recalculate("expected_action", "Запишитесь на консультацию")
        self.assertEqual(engine.decisions["action"].state.value, "Revised")
        self.assertEqual(engine.decisions["hierarchy"].state.value, "Revised")
        self.assertEqual(engine.decisions["message"].state.value, "Draft")

    def test_russian_run_is_localized_and_prints_task_understanding_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            arguments = [
                "visualmind_prototype.py",
                "--request", "Сделай постер FOHOW о профилактике суставов",
                "--objective", "Объяснить пользу профилактики и пригласить на консультацию",
                "--audience", "Взрослые 50+",
                "--brand", "FOHOW",
                "--product", "Утверждённый продукт FOHOW для суставов",
                "--asset-type", "Статус WhatsApp 9:16",
                "--expected-action", "Напишите в WhatsApp",
                "--trust-evidence", "Утверждённые сведения из каталога FOHOW",
                "--research", "Утверждённая локальная сводка продукта",
                "--direction", "product",
                "--output-dir", directory,
                "--auto-confirm",
            ]
            output = io.StringIO()
            with patch.object(sys, "argv", arguments), redirect_stdout(output):
                status = main()
        text = output.getvalue()
        self.assertEqual(status, 0)
        self.assertEqual(text.count("ПОНИМАНИЕ ЗАДАЧИ"), 1)
        self.assertIn("ТВОРЧЕСКИЕ НАПРАВЛЕНИЯ", text)
        self.assertIn("ТВОРЧЕСКОЕ РЕЗЮМЕ", text)
        self.assertIn("Создан цифровой материал", text)
        self.assertIn("[продукт]", text)
        self.assertNotIn("TASK UNDERSTANDING", text)
        self.assertNotIn("CREATIVE DIRECTIONS", text)
        self.assertNotIn("Generated Digital Asset", text)
        self.assertNotIn("WORKFLOW", text)
        self.assertNotIn("  Hero:", text)
        self.assertNotIn("active adult", text.lower())

    def test_analysis_stops_before_directions_when_gaps_are_blocking(self) -> None:
        arguments = [
            "visualmind_prototype.py",
            "--request", "Сделай постер FOHOW о профилактике суставов",
            "--analysis-only",
        ]
        output = io.StringIO()
        with patch.object(sys, "argv", arguments), redirect_stdout(output):
            status = main()
        text = output.getvalue()
        self.assertEqual(status, 2)
        self.assertIn("Творческое рассуждение не начато", text)
        self.assertNotIn("ТВОРЧЕСКИЕ НАПРАВЛЕНИЯ", text)
        self.assertNotIn("CREATIVE DIRECTIONS", text)


if __name__ == "__main__":
    unittest.main()
