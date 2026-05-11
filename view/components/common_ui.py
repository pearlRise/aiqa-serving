from PySide6.QtWidgets import QFrame, QScrollArea, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QPainter, QColor, QPen

class SmoothScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.target_val = 0
        self.anim = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.setDuration(400)

    def wheelEvent(self, event):
        delta_y = event.angleDelta().y()
        if not event.pixelDelta().isNull() or (delta_y != 0 and abs(delta_y) % 120 != 0):
            super().wheelEvent(event)
            self.target_val = self.verticalScrollBar().value()
            return
        bar = self.verticalScrollBar()
        if self.anim.state() != QPropertyAnimation.Running:
            self.target_val = bar.value()
        step = event.angleDelta().y()
        self.target_val = max(bar.minimum(), min(bar.maximum(), self.target_val - step))
        self.anim.setEndValue(self.target_val)
        self.anim.start()

class GlassFrame(QFrame):
    def __init__(self, radius=16, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            GlassFrame {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: {radius}px;
            }}
        """)

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