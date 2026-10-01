"""漢字を含む語の上に振り仮名を描画する。"""
import re

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QWidget


class FuriganaText(QWidget):
    def __init__(self, tokens, dark=False):
        super().__init__()
        self.tokens = tokens
        self.base_font = QFont("Yu Gothic", 14)
        self.ruby_font = QFont("Yu Gothic", 8)
        self.foreground = QColor("#e5f0ed" if dark else "#243b38")
        self.accent = QColor("#7edac0" if dark else "#168a75")
        self.setAccessibleName("日语原文与假名注音")
        self.setAccessibleDescription(" ".join(t.surface + (f"（{t.reading}）" if self.annotation(t) else "") for t in tokens))

    @staticmethod
    def annotation(token):
        return token.reading if re.search(r"[\u3400-\u9fff々]", token.surface) and token.reading not in ("", "*", token.surface) else ""

    def cells(self, width):
        base, ruby = QFontMetrics(self.base_font), QFontMetrics(self.ruby_font)
        line_height = base.height() + ruby.height() + 10
        x, y = 0, 0
        for index, token in enumerate(self.tokens):
            reading = self.annotation(token)
            cell_width = max(base.horizontalAdvance(token.surface), ruby.horizontalAdvance(reading)) + 4
            following = self.tokens[index + 1].surface if index + 1 < len(self.tokens) else ""
            reserve = base.horizontalAdvance(following) + 4 if following and all(c in "、。！？）」』】" for c in following) else 0
            if x and x + cell_width + reserve > width:
                x, y = 0, y + line_height
            yield QRectF(x, y, cell_width, line_height), token.surface, reading
            x += cell_width

    def heightForWidth(self, width):
        return max((int(rect.bottom()) for rect, _, _ in self.cells(max(1, width))), default=0)

    def sizeHint(self):
        return QSize(310, self.heightForWidth(310))

    def paintEvent(self, event):
        painter = QPainter(self)
        ruby_height = QFontMetrics(self.ruby_font).height()
        for rect, surface, reading in self.cells(self.width()):
            painter.setFont(self.ruby_font)
            painter.setPen(self.accent)
            painter.drawText(QRectF(rect.x(), rect.y(), rect.width(), ruby_height), Qt.AlignmentFlag.AlignCenter, reading)
            painter.setFont(self.base_font)
            painter.setPen(self.foreground)
            painter.drawText(QRectF(rect.x(), rect.y() + ruby_height, rect.width(), rect.height() - ruby_height - 6), Qt.AlignmentFlag.AlignCenter, surface)
