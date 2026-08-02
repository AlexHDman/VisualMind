"""VisualMind Studio GUI Prototype 0.3."""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from PySide6.QtCore import QByteArray, Qt, QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtSvgWidgets import QSvgWidget
    from PySide6.QtWidgets import (
        QApplication,
        QButtonGroup,
        QCheckBox,
        QComboBox,
        QFormLayout,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPlainTextEdit,
        QPushButton,
        QRadioButton,
        QScrollArea,
        QSizePolicy,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )
except ImportError as error:  # pragma: no cover - exercised only without GUI dependency
    raise SystemExit(
        "PySide6 не установлен. Запустите install_visualmind_gui.bat и повторите запуск."
    ) from error

from gui_controller import FORMAT_OPTIONS, StudioController
from visualmind_prototype import WorkflowBlocked


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


DARK_STYLE = """
QWidget { background: #151b22; color: #dce7ee; font-family: "Segoe UI"; font-size: 15px; }
QMainWindow { background: #10151b; }
QGroupBox { border: 1px solid #31414d; border-radius: 10px; margin-top: 14px; padding: 14px 10px 10px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #79d4d1; }
QLineEdit, QPlainTextEdit, QComboBox { background: #202933; border: 1px solid #40515f; border-radius: 7px; padding: 8px; selection-background-color: #267f88; }
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus { border: 1px solid #55bfc3; }
QPushButton { background: #245c66; border: 1px solid #3d8f98; border-radius: 7px; padding: 9px 14px; font-weight: 600; }
QPushButton:hover { background: #2d717b; }
QPushButton:disabled { background: #252d34; border-color: #37414a; color: #76848e; }
QPushButton#generateButton { background: #c96c2e; border-color: #e18a4e; color: #fff8f0; }
QPushButton#generateButton:hover { background: #db7834; }
QPushButton#generateButton:disabled { background: #42342c; border-color: #5a4638; color: #8b7c72; }
QCheckBox, QRadioButton { spacing: 9px; padding: 3px; }
QCheckBox::indicator, QRadioButton::indicator { width: 18px; height: 18px; }
QScrollArea { border: 0; }
QSplitter::handle { background: #28343e; width: 4px; }
QLabel#ready { color: #79d4d1; font-weight: 700; }
QLabel#blocked { color: #f29a5a; font-weight: 700; }
"""


class VisualMindWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.controller = StudioController()
        self._refreshing = False
        self._direction_buttons: dict[str, QRadioButton] = {}
        self.setWindowTitle("VisualMind Studio — Prototype 0.3")
        self.resize(1680, 980)
        self.setMinimumSize(1100, 720)
        self._build_ui()
        self._connect_signals()
        self.refresh()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        request_row = QHBoxLayout()
        self.request_edit = QPlainTextEdit()
        self.request_edit.setPlaceholderText("Опишите задачу обычными словами")
        self.request_edit.setMaximumHeight(100)
        self.analyze_button = QPushButton("Анализировать")
        self.analyze_button.setMinimumHeight(48)
        request_row.addWidget(self.request_edit, 1)
        request_row.addWidget(self.analyze_button)
        layout.addLayout(request_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._context_panel())
        splitter.addWidget(self._decisions_panel())
        splitter.addWidget(self._production_panel())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 5)
        splitter.setStretchFactor(2, 4)
        splitter.setSizes([360, 610, 500])
        layout.addWidget(splitter, 1)

        buttons = QHBoxLayout()
        self.recalculate_button = QPushButton("Пересчитать")
        self.confirm_direction_button = QPushButton("Подтвердить направление")
        self.generate_button = QPushButton("Сгенерировать")
        self.generate_button.setObjectName("generateButton")
        self.copy_prompt_button = QPushButton("Копировать Generation Prompt")
        self.open_folder_button = QPushButton("Открыть папку результата")
        self.new_project_button = QPushButton("Новый проект")
        for button in (
            self.recalculate_button,
            self.confirm_direction_button,
            self.generate_button,
            self.copy_prompt_button,
            self.open_folder_button,
            self.new_project_button,
        ):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.setCentralWidget(root)

    def _scroll_panel(self, content: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        return scroll

    def _context_panel(self) -> QScrollArea:
        content = QWidget()
        layout = QVBoxLayout(content)
        group = QGroupBox("Контекст")
        form = QFormLayout(group)
        self.context_edits: dict[str, QLineEdit] = {}
        for key, label in (
            ("brand", "Бренд"),
            ("theme", "Тема"),
            ("product", "Конкретный продукт"),
            ("audience", "Аудитория"),
            ("expected_action", "Ожидаемое действие"),
            ("final_cta", "Финальный текст CTA"),
        ):
            edit = QLineEdit()
            edit.setClearButtonEnabled(True)
            self.context_edits[key] = edit
            form.addRow(label, edit)
        self.format_combo = QComboBox()
        self.format_combo.addItem("Формат не определён", "")
        for label in FORMAT_OPTIONS:
            self.format_combo.addItem(label, label)
        form.addRow("Формат", self.format_combo)
        layout.addWidget(group)
        layout.addStretch()
        return self._scroll_panel(content)

    def _decisions_panel(self) -> QScrollArea:
        content = QWidget()
        layout = QVBoxLayout(content)
        gaps_group = QGroupBox("Пробелы в знаниях")
        gaps_layout = QVBoxLayout(gaps_group)
        self.gaps_text = QPlainTextEdit()
        self.gaps_text.setReadOnly(True)
        self.gaps_text.setMinimumHeight(150)
        gaps_layout.addWidget(self.gaps_text)
        layout.addWidget(gaps_group)

        self.directions_group = QGroupBox("Creative Directions")
        self.directions_layout = QVBoxLayout(self.directions_group)
        layout.addWidget(self.directions_group)

        summary_group = QGroupBox("Creative Summary")
        summary_layout = QVBoxLayout(summary_group)
        self.summary_text = QPlainTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMinimumHeight(230)
        summary_layout.addWidget(self.summary_text)
        layout.addWidget(summary_group)

        checks_group = QGroupBox("Подтверждения")
        checks_layout = QVBoxLayout(checks_group)
        self.confirmation_checks: dict[str, QCheckBox] = {}
        for key, label in (
            ("product", "Продукт подтверждён"),
            ("audience", "Аудитория подтверждена"),
            ("display_cta", "Display CTA подтверждён"),
            ("format", "Формат подтверждён"),
            ("verified_facts", "Использовать только проверенные факты"),
            ("direction", "Творческое направление подтверждено"),
        ):
            checkbox = QCheckBox(label)
            self.confirmation_checks[key] = checkbox
            checks_layout.addWidget(checkbox)
        layout.addWidget(checks_group)
        layout.addStretch()
        return self._scroll_panel(content)

    def _production_panel(self) -> QScrollArea:
        content = QWidget()
        layout = QVBoxLayout(content)
        preview_group = QGroupBox("SVG Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.svg_preview = QSvgWidget()
        self.svg_preview.setMinimumHeight(320)
        self.svg_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preview_layout.addWidget(self.svg_preview)
        layout.addWidget(preview_group, 2)

        spec_group = QGroupBox("Generation Specification")
        spec_layout = QVBoxLayout(spec_group)
        self.spec_text = QPlainTextEdit()
        self.spec_text.setReadOnly(True)
        self.spec_text.setMinimumHeight(200)
        spec_layout.addWidget(self.spec_text)
        layout.addWidget(spec_group)

        readiness_group = QGroupBox("Production Readiness")
        readiness_layout = QVBoxLayout(readiness_group)
        self.readiness_label = QLabel()
        self.readiness_label.setWordWrap(True)
        readiness_layout.addWidget(self.readiness_label)
        layout.addWidget(readiness_group)
        layout.addStretch()
        return self._scroll_panel(content)

    def _connect_signals(self) -> None:
        self.analyze_button.clicked.connect(self.analyze)
        self.request_edit.textChanged.connect(self.mark_request_dirty)
        self.recalculate_button.clicked.connect(self.recalculate)
        self.confirm_direction_button.clicked.connect(self.confirm_direction)
        self.generate_button.clicked.connect(self.generate)
        self.copy_prompt_button.clicked.connect(self.copy_prompt)
        self.open_folder_button.clicked.connect(self.open_output_folder)
        self.new_project_button.clicked.connect(self.new_project)
        for field_name, edit in self.context_edits.items():
            edit.textEdited.connect(lambda _value, name=field_name: self.mark_dirty(name))
        self.format_combo.currentIndexChanged.connect(lambda _index: self.mark_dirty("format"))
        for key, checkbox in self.confirmation_checks.items():
            checkbox.toggled.connect(lambda checked, name=key: self.set_confirmation(name, checked))

    def show_error(self, title: str, error: Exception) -> None:
        QMessageBox.warning(self, title, str(error))

    def analyze(self) -> None:
        try:
            self.controller.analyze(self.request_edit.toPlainText())
        except (ValueError, WorkflowBlocked) as error:
            self.show_error("Анализ не выполнен", error)
            return
        self.refresh()

    def mark_dirty(self, field_name: str) -> None:
        if self._refreshing or self.controller.engine is None:
            return
        try:
            self.controller.invalidate_field(field_name)
        except ValueError:
            return
        self.refresh_confirmations_and_readiness()

    def mark_request_dirty(self) -> None:
        if self._refreshing:
            return
        self.controller.invalidate_request(self.request_edit.toPlainText())
        self.refresh_confirmations_and_readiness()

    def recalculate(self) -> None:
        if self.controller.engine is None:
            self.show_error("Пересчёт недоступен", WorkflowBlocked("Сначала выполните анализ задачи."))
            return
        try:
            current = self.controller.fields()
            values = {
                "brand": self.context_edits["brand"].text(),
                "theme": self.context_edits["theme"].text(),
                "product": self.context_edits["product"].text(),
                "audience": self.context_edits["audience"].text(),
                "expected_action": self.context_edits["expected_action"].text(),
                "final_cta": self.context_edits["final_cta"].text(),
                "format": self.format_combo.currentData() or "",
            }
            lookup = {"theme": "topic", "final_cta": "display_cta"}
            for field_name, value in values.items():
                current_key = lookup.get(field_name, field_name)
                if value.strip() != current[current_key].strip():
                    self.controller.update_field(field_name, value)
        except (ValueError, WorkflowBlocked) as error:
            self.show_error("Пересчёт не выполнен", error)
        self.refresh()

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _refresh_directions(self) -> None:
        self._clear_layout(self.directions_layout)
        self._direction_buttons = {}
        engine = self.controller.engine
        if engine is None or not engine.directions:
            label = QLabel("Направления появятся после закрытия блокирующих пробелов.")
            label.setWordWrap(True)
            self.directions_layout.addWidget(label)
            return
        group = QButtonGroup(self.directions_group)
        group.setExclusive(True)
        for direction in engine.directions:
            card = QFrame()
            card.setFrameShape(QFrame.Shape.StyledPanel)
            card_layout = QVBoxLayout(card)
            radio = QRadioButton(direction.name)
            radio.setChecked(direction.direction_id == engine.selected_direction_id)
            radio.toggled.connect(
                lambda checked, direction_id=direction.direction_id: self.select_direction(direction_id) if checked else None
            )
            group.addButton(radio)
            self._direction_buttons[direction.direction_id] = radio
            details = QLabel(
                f"Идея: {direction.core_idea}\n\n"
                f"Визуальный герой: {direction.hero}\n\n"
                f"Обоснование: {direction.rationale}\n\n"
                f"Риск: {direction.risk}"
            )
            details.setWordWrap(True)
            card_layout.addWidget(radio)
            card_layout.addWidget(details)
            self.directions_layout.addWidget(card)

    def select_direction(self, direction_id: str) -> None:
        if self._refreshing:
            return
        try:
            self.controller.select_direction(direction_id)
        except (ValueError, WorkflowBlocked) as error:
            self.show_error("Направление недоступно", error)
            return
        self.refresh_summary_and_readiness()

    def confirm_direction(self) -> None:
        engine = self.controller.engine
        if engine is None or engine.selected_direction_id is None:
            self.show_error("Подтверждение недоступно", WorkflowBlocked("Сначала выберите творческое направление."))
            return
        self.controller.set_confirmation("direction", True)
        self.refresh_confirmations_and_readiness()

    def set_confirmation(self, key: str, checked: bool) -> None:
        if self._refreshing:
            return
        self.controller.set_confirmation(key, checked)
        self.refresh_confirmations_and_readiness()

    def generate(self) -> None:
        try:
            asset, _trace, _prompt = self.controller.generate(OUTPUT_DIR)
        except (ValueError, WorkflowBlocked, OSError) as error:
            self.show_error("Генерация остановлена", error)
            self.refresh_confirmations_and_readiness()
            return
        self.svg_preview.load(str(asset))
        self.refresh_summary_and_readiness()

    def copy_prompt(self) -> None:
        if not self.controller.state.prompt_text:
            self.show_error("Промпт недоступен", WorkflowBlocked("Сначала выполните успешную генерацию."))
            return
        QApplication.clipboard().setText(self.controller.state.prompt_text)

    def open_output_folder(self) -> None:
        path = self.controller.state.generated_asset.parent if self.controller.state.generated_asset else OUTPUT_DIR
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

    def new_project(self) -> None:
        self.controller.new_project()
        self.request_edit.clear()
        self.svg_preview.load(QByteArray())
        self.refresh()

    def refresh_summary_and_readiness(self) -> None:
        self.summary_text.setPlainText(self.controller.creative_summary())
        self.spec_text.setPlainText(self.controller.generation_preview())
        self.refresh_confirmations_and_readiness()

    def refresh_confirmations_and_readiness(self) -> None:
        self._refreshing = True
        for key, checkbox in self.confirmation_checks.items():
            checkbox.setChecked(self.controller.state.confirmations[key])
        self._refreshing = False
        issues = self.controller.readiness_issues()
        if issues:
            self.readiness_label.setObjectName("blocked")
            self.readiness_label.setText("НЕ ГОТОВО\n\n" + "\n".join(f"• {issue}" for issue in issues))
        else:
            self.readiness_label.setObjectName("ready")
            self.readiness_label.setText("ГОТОВО К ПРОИЗВОДСТВУ")
        self.readiness_label.style().unpolish(self.readiness_label)
        self.readiness_label.style().polish(self.readiness_label)
        self.generate_button.setEnabled(self.controller.can_generate)
        self.copy_prompt_button.setEnabled(bool(self.controller.state.prompt_text))
        self.open_folder_button.setEnabled(self.controller.state.generated_asset is not None)

    def refresh(self) -> None:
        self._refreshing = True
        fields = self.controller.fields()
        field_lookup = {"theme": "topic", "final_cta": "display_cta"}
        for key, edit in self.context_edits.items():
            edit.setText(fields[field_lookup.get(key, key)])
        index = self.format_combo.findData(fields["format"])
        self.format_combo.setCurrentIndex(max(index, 0))
        blockers = self.controller.blocking_gap_fields()
        blocker_lookup = {"theme": "topic", "final_cta": "display_cta"}
        for key, edit in self.context_edits.items():
            blocking = blocker_lookup.get(key, key) in blockers
            edit.setStyleSheet("border: 1px solid #e58a4a;" if blocking else "")
        self.format_combo.setStyleSheet("border: 1px solid #e58a4a;" if "format" in blockers else "")
        self.gaps_text.setPlainText("\n\n".join(self.controller.knowledge_gaps()) or "Пробелы не обнаружены.")
        self._refreshing = False
        self._refresh_directions()
        self.refresh_summary_and_readiness()


def main() -> int:
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    window = VisualMindWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
