import unittest
from types import SimpleNamespace

from gui_controller import StudioController
from visualmind_prototype import CreativeEngine, build_context, parse_natural_request


FULL_REQUEST = (
    "Сделай вертикальный постер 9:16 для WhatsApp о продукте «Кальций FOHOW». "
    "Аудитория — мужчины и женщины старше 50 лет. "
    "Тема — профилактика остеопороза и сохранение активной жизни. "
    "Призыв: «Напишите нам в WhatsApp»."
)


def cli_args(request: str) -> SimpleNamespace:
    return SimpleNamespace(
        request=request,
        auto_confirm=True,
        objective="",
        audience="",
        brand="",
        product="",
        asset_type="",
        expected_action="",
        channel="",
        width=0,
        height=0,
        display_cta="",
        trust_evidence="",
        research="",
    )


class NaturalRequestParserTests(unittest.TestCase):
    def test_full_russian_request_extracts_all_explicit_context(self) -> None:
        parsed = parse_natural_request(FULL_REQUEST)
        self.assertEqual(parsed.brand, "FOHOW")
        self.assertEqual(parsed.product, "Кальций FOHOW")
        self.assertEqual(parsed.audience, "мужчины и женщины старше 50 лет")
        self.assertEqual(parsed.topic, "профилактика остеопороза и сохранение активной жизни")
        self.assertEqual(parsed.expected_action, "написать в WhatsApp")
        self.assertEqual(parsed.display_cta, "Напишите нам в WhatsApp")
        self.assertEqual(parsed.asset_type, "Статус WhatsApp 9:16")

    def test_straight_quotes_are_supported_without_brand_specific_logic(self) -> None:
        request = (
            'Создай квадратный постер 1:1 о продукте "Omega Plus". '
            'Аудитория — взрослые старше 40 лет. '
            'Тема — поддержка активного образа жизни. '
            'CTA: "Закажите консультацию".'
        )
        parsed = parse_natural_request(request)
        self.assertEqual(parsed.product, "Omega Plus")
        self.assertEqual(parsed.audience, "взрослые старше 40 лет")
        self.assertEqual(parsed.topic, "поддержка активного образа жизни")
        self.assertEqual(parsed.expected_action, "заказать консультацию")
        self.assertEqual(parsed.display_cta, "Закажите консультацию")

    def test_sentence_order_does_not_change_extraction(self) -> None:
        request = (
            "CTA: “Напишите нам в WhatsApp”. "
            "Тема — профилактика остеопороза и сохранение активной жизни. "
            "Продукт «Кальций FOHOW». "
            "Для мужчин и женщин старше 50 лет нужен вертикальный WhatsApp-постер 9:16."
        )
        parsed = parse_natural_request(request)
        self.assertEqual(parsed.product, "Кальций FOHOW")
        self.assertEqual(parsed.audience, "мужчин и женщин старше 50 лет")
        self.assertEqual(parsed.expected_action, "написать в WhatsApp")
        self.assertEqual(parsed.display_cta, "Напишите нам в WhatsApp")

    def test_missing_cta_remains_a_blocking_gap(self) -> None:
        request = (
            "Создай постер о продукте «Кальций FOHOW». "
            "Аудитория — мужчины и женщины старше 50 лет. Тема — профилактика остеопороза."
        )
        controller = StudioController()
        controller.analyze(request)
        self.assertEqual(controller.context.expected_action, "")
        self.assertEqual(controller.context.display_cta, "")
        self.assertIn("expected_action", controller.blocking_gap_fields())

    def test_missing_audience_remains_a_blocking_gap(self) -> None:
        request = (
            "Создай постер о продукте «Кальций FOHOW». "
            "Тема — профилактика остеопороза. Призыв: «Напишите нам в WhatsApp»."
        )
        controller = StudioController()
        controller.analyze(request)
        self.assertEqual(controller.context.audience, "")
        self.assertIn("audience", controller.blocking_gap_fields())
        self.assertIn("format", controller.blocking_gap_fields())

    def test_action_label_produces_intent_and_professional_display_copy(self) -> None:
        request = "Продукт «Omega Plus». Аудитория — взрослые. Действие: написать в WhatsApp."
        parsed = parse_natural_request(request)
        self.assertEqual(parsed.expected_action, "написать в WhatsApp")
        self.assertEqual(parsed.display_cta, "Напишите в WhatsApp")

    def test_brand_is_not_accepted_as_product(self) -> None:
        request = (
            "Бренд — «Aurora». Продукт «Aurora». "
            "Аудитория — взрослые старше 40 лет. CTA: «Узнайте подробнее»."
        )
        parsed = parse_natural_request(request)
        self.assertEqual(parsed.brand, "Aurora")
        self.assertEqual(parsed.product, "")
        controller = StudioController()
        controller.analyze(request)
        self.assertIn("product", controller.blocking_gap_fields())

    def test_cli_and_gui_controller_use_identical_parsed_context(self) -> None:
        cli_context = build_context(cli_args(FULL_REQUEST))
        CreativeEngine(cli_context)
        controller = StudioController()
        controller.analyze(FULL_REQUEST)
        gui_context = controller.context
        for field in (
            "brand", "product", "audience", "topic", "expected_action",
            "display_cta", "channel", "asset_type", "width", "height",
        ):
            with self.subTest(field=field):
                self.assertEqual(getattr(cli_context, field), getattr(gui_context, field))
        self.assertIn("trust_evidence", {gap.field for gap in controller.engine.knowledge_gaps})


if __name__ == "__main__":
    unittest.main()
