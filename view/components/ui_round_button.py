from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen

class SmoothRoundButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(26, 26)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(51, 51, 51) if self.isDown() else QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255, 25), 1.0))
        painter.drawEllipse(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1))
        super().paintEvent(event)