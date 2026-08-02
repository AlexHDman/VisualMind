import importlib.util
import os
import unittest


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE_AVAILABLE = importlib.util.find_spec("PySide6") is not None

if PYSIDE_AVAILABLE:
    from PySide6.QtCore import QByteArray
    from PySide6.QtWidgets import QApplication, QGroupBox, QPushButton

    from gui_app import (
        DARK_STYLE,
        AspectRatioSvgPreview,
        VisualMindWindow,
        keep_aspect_ratio_rect,
    )


REQUEST = (
    "Сделай вертикальный постер 9:16 для WhatsApp о продукте «Кальций FOHOW». "
    "Аудитория — мужчины и женщины старше 50 лет. "
    "Тема — профилактика остеопороза и сохранение активной жизни. "
    "Призыв: «Напишите нам в WhatsApp»."
)


@unittest.skipUnless(PYSIDE_AVAILABLE, "PySide6 не установлен")
class GuiPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(DARK_STYLE)

    def test_keep_aspect_ratio_for_vertical_and_landscape(self) -> None:
        vertical = keep_aspect_ratio_rect(1080, 1920, 600, 400)
        self.assertAlmostEqual(vertical[0], 187.5)
        self.assertAlmostEqual(vertical[1], 0.0)
        self.assertAlmostEqual(vertical[2], 225.0)
        self.assertAlmostEqual(vertical[3], 400.0)
        landscape = keep_aspect_ratio_rect(1200, 628, 600, 400)
        self.assertAlmostEqual(landscape[0], 0.0)
        self.assertAlmostEqual(landscape[1], 43.0)
        self.assertAlmostEqual(landscape[2], 600.0)
        self.assertAlmostEqual(landscape[3], 314.0)

    def test_preview_recalculates_centred_viewport_after_resize(self) -> None:
        preview = AspectRatioSvgPreview()
        svg = QByteArray(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920"/>')
        self.assertTrue(preview.load(svg))
        preview.resize(600, 400)
        first = preview.fitted_viewport()
        self.assertAlmostEqual(first.width() / first.height(), 1080 / 1920)
        self.assertAlmostEqual(first.center().x(), preview.width() / 2, delta=1.0)
        self.assertAlmostEqual(first.center().y(), preview.height() / 2, delta=1.0)
        preview.resize(400, 600)
        second = preview.fitted_viewport()
        self.assertAlmostEqual(second.width() / second.height(), 1080 / 1920)
        self.assertAlmostEqual(second.center().x(), preview.width() / 2, delta=1.0)
        self.assertAlmostEqual(second.center().y(), preview.height() / 2, delta=1.0)

    def test_direction_radio_and_card_update_together(self) -> None:
        window = VisualMindWindow()
        window.request_edit.setPlainText(REQUEST)
        window.analyze()
        self.assertEqual(len(window._direction_buttons), 3)
        initial = window.controller.engine.selected_direction_id
        self.assertTrue(window._direction_buttons[initial].isChecked())
        self.assertTrue(window._direction_cards[initial].property("selected"))
        window._direction_buttons["trust"].click()
        self.app.processEvents()
        self.assertEqual(window.controller.engine.selected_direction_id, "trust")
        self.assertTrue(window._direction_buttons["trust"].isChecked())
        self.assertTrue(window._direction_buttons["trust"].property("selected"))
        self.assertTrue(window._direction_cards["trust"].property("selected"))
        for direction_id, card in window._direction_cards.items():
            if direction_id != "trust":
                self.assertFalse(card.property("selected"))
                self.assertFalse(window._direction_buttons[direction_id].property("selected"))
        window.close()

    def test_user_facing_gui_headings_are_localized(self) -> None:
        window = VisualMindWindow()
        group_titles = {group.title() for group in window.findChildren(QGroupBox)}
        button_texts = {button.text() for button in window.findChildren(QPushButton)}
        self.assertTrue({
            "Творческие направления",
            "Творческое резюме",
            "Предпросмотр SVG",
            "Спецификация генерации",
            "Готовность к производству",
        }.issubset(group_titles))
        self.assertFalse({
            "Creative Directions",
            "Creative Summary",
            "SVG Preview",
            "Generation Specification",
            "Production Readiness",
        } & group_titles)
        self.assertIn("Копировать промпт генерации", button_texts)
        self.assertNotIn("Копировать Generation Prompt", button_texts)
        window.close()


if __name__ == "__main__":
    unittest.main()
