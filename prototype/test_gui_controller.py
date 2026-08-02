import tempfile
import unittest
from pathlib import Path

from gui_controller import StudioController


REQUEST = "Сделай постер FOHOW о профилактике суставов"


def completed_controller(include_format: bool = True) -> StudioController:
    controller = StudioController()
    controller.analyze(REQUEST)
    controller.update_field("product", "Утверждённый продукт FOHOW для суставов")
    controller.update_field("audience", "Взрослые 50+")
    controller.update_field("expected_action", "смотри whatsapp")
    if include_format:
        controller.update_field("format", "WhatsApp 9:16 — 1080×1920")
        controller.select_direction("prevention")
    return controller


def confirm_all(controller: StudioController) -> None:
    for key in controller.state.confirmations:
        controller.set_confirmation(key, True)


class StudioControllerTests(unittest.TestCase):
    def test_initial_state(self) -> None:
        controller = StudioController()
        self.assertIsNone(controller.engine)
        self.assertFalse(controller.can_generate)
        self.assertEqual(controller.state.request, "")
        self.assertTrue(all(not value for value in controller.state.confirmations.values()))

    def test_blocking_gaps_disable_generate(self) -> None:
        controller = StudioController()
        controller.analyze(REQUEST)
        self.assertFalse(controller.can_generate)
        self.assertTrue({"product", "audience", "expected_action", "format"}.issubset(controller.blocking_gap_fields()))

    def test_product_equal_to_brand_disables_generate(self) -> None:
        controller = StudioController()
        controller.analyze(REQUEST)
        controller.update_field("product", "fohow")
        controller.update_field("audience", "Взрослые 50+")
        controller.update_field("expected_action", "Напишите в WhatsApp")
        controller.update_field("format", "WhatsApp 9:16 — 1080×1920")
        confirm_all(controller)
        self.assertFalse(controller.can_generate)
        self.assertTrue(any("Продукт" in issue for issue in controller.readiness_issues()))

    def test_missing_format_disables_generate(self) -> None:
        controller = completed_controller(include_format=False)
        confirm_all(controller)
        self.assertFalse(controller.can_generate)
        self.assertIn("format", controller.blocking_gap_fields())

    def test_field_change_resets_only_dependent_confirmations(self) -> None:
        controller = completed_controller()
        confirm_all(controller)
        controller.update_field("audience", "Активные взрослые 55–70 лет")
        self.assertFalse(controller.state.confirmations["audience"])
        self.assertFalse(controller.state.confirmations["direction"])
        self.assertTrue(controller.state.confirmations["product"])
        self.assertTrue(controller.state.confirmations["display_cta"])
        self.assertTrue(controller.state.confirmations["format"])
        self.assertTrue(controller.state.confirmations["verified_facts"])

    def test_changed_request_requires_new_analysis(self) -> None:
        controller = completed_controller()
        confirm_all(controller)
        self.assertTrue(controller.can_generate)
        controller.invalidate_request("Сделай другой постер FOHOW")
        self.assertFalse(controller.can_generate)
        self.assertFalse(controller.state.confirmations["direction"])

    def test_all_confirmations_enable_generate(self) -> None:
        controller = completed_controller()
        self.assertFalse(controller.can_generate)
        confirm_all(controller)
        self.assertTrue(controller.can_generate, controller.readiness_issues())

    def test_generation_creates_svg_json_and_txt(self) -> None:
        controller = completed_controller()
        confirm_all(controller)
        with tempfile.TemporaryDirectory() as directory:
            asset, trace, prompt = controller.generate(Path(directory), "studio-test")
            self.assertTrue(asset.exists())
            self.assertTrue(trace.exists())
            self.assertTrue(prompt.exists())
            self.assertEqual({asset.suffix, trace.suffix, prompt.suffix}, {".svg", ".json", ".txt"})
            prompt_text = prompt.read_text(encoding="utf-8")
            self.assertIn("Утверждённый продукт FOHOW для суставов", prompt_text)
            self.assertIn("Подробнее в WhatsApp", prompt_text)
            self.assertIn("не добавлять неподтверждённые", prompt_text)

    def test_new_project_clears_state(self) -> None:
        controller = completed_controller()
        confirm_all(controller)
        controller.new_project()
        self.assertIsNone(controller.engine)
        self.assertIsNone(controller.context)
        self.assertEqual(controller.state.request, "")
        self.assertFalse(controller.can_generate)
        self.assertTrue(all(not value for value in controller.state.confirmations.values()))


if __name__ == "__main__":
    unittest.main()
