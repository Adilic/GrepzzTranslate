from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

app = QApplication([])
window = QWidget()
window.setWindowTitle("GrepzzTranslate · 阅读测试页")
window.setStyleSheet("QWidget { background: #fcfaf5; color: #223832; } QLabel { font-family: 'Segoe UI', 'Yu Gothic'; }")
layout = QVBoxLayout(window)
layout.setContentsMargins(48, 36, 48, 36)
layout.setSpacing(20)
for text, size in [("截图阅读测试", 20), ("按 Alt + Q，框选下方单词，松开鼠标。", 16),
                   ("considerable", 38), ("deteriorated", 38), ("経験", 38), ("経験を積む", 38)]:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setStyleSheet(f"font-size: {size}px;")
    layout.addWidget(label)
window.resize(680, 540)
window.show()
app.exec()
