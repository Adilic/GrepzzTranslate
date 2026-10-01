from dataclasses import replace

from PySide6.QtCore import QEvent, QPoint, QRect, Qt, Signal, Slot
from PySide6.QtGui import QColor, QCursor, QKeyEvent, QKeySequence
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                               QFormLayout, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget)

from .config import Config
from .models import LookupResult
from .outside_click import OutsideClickMonitor
from .furigana import FuriganaText


class OCRCorrectionEdit(QLineEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setMaxLength(2000)
        self.setPlaceholderText("修正识别原文，按 Enter 重查")
        self.setAccessibleName("OCR 识别原文，可用键盘修正")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # 修正欄でもクリップボードは使用しない。
        if any(event.matches(key) for key in (QKeySequence.StandardKey.Paste, QKeySequence.StandardKey.Copy, QKeySequence.StandardKey.Cut)):
            event.accept()
            return
        super().keyPressEvent(event)


def clamp_position(anchor: QRect, size, available: QRect) -> QPoint:
    x = anchor.left()
    y = anchor.bottom() + 12
    if y + size.height() > available.bottom() + 1:
        y = anchor.top() - size.height() - 12
    return QPoint(max(available.left(), min(x, available.right() - size.width() + 1)),
                  max(available.top(), min(y, available.bottom() - size.height() + 1)))


class LookupPopup(QWidget):
    dismissed = Signal()
    lookup_requested = Signal(str)
    recapture_requested = Signal()

    def __init__(self, theme: str = "light") -> None:
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("GrepzzTranslate")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.anchor = QRect()
        self.theme = theme
        self._presenting = False
        self.monitor = OutsideClickMonitor(self)
        self.destroyed.connect(self.monitor.stop)
        self.monitor.clicked.connect(self.on_outside_click, Qt.ConnectionType.QueuedConnection)
        QApplication.instance().installEventFilter(self)
        if theme == "light":
            bg, fg, muted, accent, soft, border = "#ffffff", "#243b38", "#82928e", "#168a75", "#edf8f4", "#e3ece8"
        else:
            bg, fg, muted, accent, soft, border = "#1e2a2a", "#e5f0ed", "#97aca5", "#7edac0", "#293c36", "#344743"
        self.setStyleSheet(f"""
            QWidget {{ color: {fg}; font-family: 'Segoe UI', 'Microsoft YaHei UI', 'Yu Gothic UI'; font-size: 14px; }}
            QFrame#card {{ background: {bg}; border: 1px solid {border}; border-radius: 18px; }}
            QLabel, QWidget#content, QScrollArea {{ background: transparent; border: none; }}
            QLabel#brand {{ color: {muted}; font-size: 12px; font-weight: 600; }}
            QLabel#mark {{ background: {soft}; color: {accent}; border-radius: 8px; font-size: 14px; font-weight: 700; }}
            QLabel#language {{ color: {accent}; font-size: 11px; font-weight: 600; }}
            QLabel#heading {{ font-size: 27px; font-weight: 600; }}
            QLabel#reading {{ color: {accent}; font-size: 16px; }}
            QLabel#meaning {{ font-size: 17px; }}
            QLabel#muted {{ color: {muted}; font-size: 12px; }}
            QLabel#pos {{ color: {accent}; font-size: 12px; }}
            QLabel#footer {{ color: {muted}; font-size: 11px; }}
            QFrame#divider {{ background: {border}; border: none; }}
            QPushButton {{ background: {soft}; color: {accent}; border: none; border-radius: 8px; padding: 7px 10px; text-align: left; }}
            QPushButton:hover {{ background: {border}; }}
            QPushButton#edit {{ background: transparent; color: {muted}; font-size: 11px; padding: 4px 6px; }}
            QPushButton#edit:hover, QPushButton#edit:checked {{ background: {soft}; color: {accent}; }}
            QLineEdit {{ background: {soft}; border: 1px solid {border}; border-radius: 8px; padding: 8px 10px; selection-background-color: {accent}; }}
            QScrollBar:vertical {{ background: transparent; width: 5px; margin: 0; }}
            QScrollBar::handle:vertical {{ background: {border}; border-radius: 2px; min-height: 24px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 16)
        self.card = QFrame()
        self.card.setObjectName("card")
        outer.addWidget(self.card)
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(26, 57, 47, 35))
        self.card.setGraphicsEffect(shadow)
        self.layout_card = QVBoxLayout(self.card)
        self.layout_card.setContentsMargins(22, 18, 22, 16)
        self.layout_card.setSpacing(14)
        header = QHBoxLayout()
        header.setSpacing(8)
        mark = QLabel("G")
        mark.setObjectName("mark")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(26, 26)
        header.addWidget(mark)
        brand = QLabel("GrepzzTranslate")
        brand.setObjectName("brand")
        header.addWidget(brand)
        header.addStretch()
        self.language = QLabel()
        self.language.setObjectName("language")
        header.addWidget(self.language)
        self.edit_button = QPushButton("修正")
        self.edit_button.setObjectName("edit")
        self.edit_button.setCheckable(True)
        self.edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_button.toggled.connect(self.toggle_editor)
        header.addWidget(self.edit_button)
        self.layout_card.addLayout(header)
        self.editor = OCRCorrectionEdit()
        self.editor.returnPressed.connect(self.submit_correction)
        self.editor.hide()
        self.layout_card.addWidget(self.editor)
        self.scroll = QScrollArea()
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content = QWidget()
        self.content.setObjectName("content")
        self.body = QVBoxLayout(self.content)
        self.body.setContentsMargins(0, 2, 6, 4)
        self.body.setSpacing(10)
        self.scroll.setWidget(self.content)
        self.layout_card.addWidget(self.scroll)
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFixedHeight(1)
        self.layout_card.addWidget(divider)
        footer = QHBoxLayout()
        self.source = QLabel("本地查询")
        self.source.setObjectName("footer")
        footer.addWidget(self.source)
        footer.addStretch()
        hint = QLabel("点击外部收起")
        hint.setObjectName("footer")
        footer.addWidget(hint)
        self.layout_card.addLayout(footer)

    def clear(self) -> None:
        self.edit_button.blockSignals(True)
        self.edit_button.setChecked(False)
        self.edit_button.blockSignals(False)
        self.editor.hide()
        self.edit_button.hide()
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()

    def label(self, text: str, name: str = "") -> None:
        label = QLabel(text)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setWordWrap(True)
        label.setObjectName(name)
        self.body.addWidget(label)

    def show_result(self, result: LookupResult, anchor: QRect) -> None:
        self.clear()
        self.editor.setText(result.normalized_text)
        self.edit_button.setVisible(bool(result.normalized_text))
        self.language.setText({"English": "EN", "Japanese": "日本語"}.get(result.language, ""))
        self.source.setText(result.source.split(" · ")[0] or "本地查询")
        self.source.setToolTip(result.source)
        annotated = result.language == "Japanese" and bool(result.tokens)
        if annotated:
            self.label("日语原文 · 假名注音", "pos")
            self.body.addWidget(FuriganaText(result.tokens, self.theme == "dark"))
            if result.meaning:
                self.label("中文译文" if result.translated else "词典释义", "pos")
                self.label(result.meaning, "meaning")
        elif result.translated:
            self.label(result.meaning or "", "meaning")
            self.label("原文", "pos")
            self.label(result.normalized_text, "muted")
        else:
            self.label(result.headword or result.normalized_text or "没有识别到文字", "heading")
        if result.reading and not annotated:
            self.label(result.reading, "reading")
        if result.phonetic:
            self.label(result.phonetic, "reading")
        if result.part_of_speech:
            self.label(result.part_of_speech, "pos")
        if result.meaning and not result.translated and not annotated:
            self.label(result.meaning, "meaning")
        if result.message:
            self.label(result.message, "muted")
        for component in result.components:
            self.label(component.headword or component.normalized_text, "reading")
            self.label(component.meaning or "", "meaning")
        if result.suggestions:
            self.label("你可能想查", "muted")
            for suggestion in result.suggestions:
                button = QPushButton(suggestion)
                button.clicked.connect(lambda checked=False, text=suggestion: self.lookup_requested.emit(text))
                self.body.addWidget(button)
        if not result.normalized_text:
            button = QPushButton("重新框选")
            button.clicked.connect(self.recapture_requested.emit)
            self.body.addWidget(button)
        if result.headword and result.headword.casefold() != result.normalized_text.casefold():
            self.label(f"原文  {result.normalized_text}", "muted")
        self.present(anchor)

    def show_message(self, message: str, anchor: QRect) -> None:
        self.clear()
        self.language.clear()
        self.source.setText("本地处理")
        self.label(message, "muted")
        self.present(anchor)

    def fit_content(self) -> None:
        screen = QApplication.screenAt(self.anchor.center()) or QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        available = screen.availableGeometry()
        width = min(400, available.width())
        content_width = max(80, width - 72)
        self.content.setFixedWidth(content_width)
        height = 6
        for index in range(self.body.count()):
            widget = self.body.itemAt(index).widget()
            widget.ensurePolished()
            widget.setFixedWidth(content_width - 6)
            height += max(widget.sizeHint().height(), widget.heightForWidth(content_width - 6))
        height += max(0, self.body.count() - 1) * self.body.spacing()
        self.content.setMinimumHeight(height)
        self.body.invalidate()
        self.body.activate()
        overhead = 151 + (52 if self.editor.isVisibleTo(self.card) else 0)
        self.resize(width, min(max(180, height + overhead), 580, available.height()))
        self.move(clamp_position(self.anchor, self.size(), available))

    def present(self, anchor: QRect) -> None:
        self._presenting = True
        self.anchor = anchor
        was_visible = self.isVisible()
        self.fit_content()
        self.show()
        if not was_visible:
            self.raise_()
            self.activateWindow()
            self.setFocus()
            self.monitor.start(int(self.winId()))
        self._presenting = False

    def toggle_editor(self, visible: bool) -> None:
        self.editor.setVisible(visible)
        self.fit_content()
        if visible:
            self.editor.setFocus()

    def dismiss(self) -> None:
        if self.isVisible():
            self.hide()
            self.dismissed.emit()

    @Slot(int)
    def on_outside_click(self, generation: int) -> None:
        if generation == self.monitor.generation:
            self.dismiss()

    def event(self, event) -> bool:
        if event.type() == QEvent.Type.WindowDeactivate and not getattr(self, "_presenting", True):
            self.dismiss()
        return super().event(event)

    def eventFilter(self, watched, event) -> bool:
        if self.isVisible() and event.type() == QEvent.Type.MouseButtonPress:
            if isinstance(watched, QWidget) and watched is not self and not self.isAncestorOf(watched):
                self.dismiss()
        return False

    def hideEvent(self, event) -> None:
        self.monitor.stop()
        super().hideEvent(event)

    def submit_correction(self) -> None:
        text = self.editor.text().strip()
        if text:
            self.lookup_requested.emit(text)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.dismiss()
        else:
            super().keyPressEvent(event)


class SettingsDialog(QDialog):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.setWindowTitle("GrepzzTranslate · 设置")
        self.config = config
        layout = QFormLayout(self)
        self.hotkey = QLineEdit(config.capture_hotkey)
        layout.addRow("截图快捷键", self.hotkey)
        self.position = QComboBox()
        self.position.addItems(["capture", "cursor"])
        self.position.setCurrentText(config.popup_position)
        layout.addRow("浮窗位置", self.position)
        self.theme = QComboBox()
        self.theme.addItems(["light", "dark"])
        self.theme.setCurrentText(config.theme)
        layout.addRow("主题", self.theme)
        self.log_text = QCheckBox("在日志中保存 OCR 原文")
        self.log_text.setChecked(config.log_ocr_text)
        layout.addRow(self.log_text)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def value(self) -> Config:
        config = replace(self.config, capture_hotkey=self.hotkey.text().strip(), popup_position=self.position.currentText(),
                         theme=self.theme.currentText(), log_ocr_text=self.log_text.isChecked())
        config.validate()
        return config
