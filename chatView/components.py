import math
from PySide6.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, QTextEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPainterPath, QColor, QTextOption

# 말풍선 배경 프레임
class BubbleFrame(QFrame):
    def __init__(self, is_me):
        super().__init__()
        self.is_me = is_me
        self.has_tail = True
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        
        w, h = self.width(), self.height()
        r, t = 16, 10 

        if self.has_tail:
            if self.is_me:
                path.moveTo(r, 0)
                path.lineTo(w - r - t, 0)
                path.quadTo(w - t, 0, w - t, r)
                path.lineTo(w - t, h - 14)
                path.cubicTo(w - t, h - 8, w - t + 4, h - 2, w, h)
                path.quadTo(w - t + 2, h, w - t - 12, h)
                path.lineTo(r, h)
                path.quadTo(0, h, 0, h - r)
                path.lineTo(0, r)
                path.quadTo(0, 0, r, 0)
            else:
                path.moveTo(t + r, 0)
                path.lineTo(w - r, 0)
                path.quadTo(w, 0, w, r)
                path.lineTo(w, h - r)
                path.quadTo(w, h, w - r, h)
                path.lineTo(t + 12, h)
                path.quadTo(t - 2, h, 0, h)
                path.cubicTo(t - 4, h - 2, t, h - 8, t, h - 14)
                path.lineTo(t, r)
                path.quadTo(t, 0, t + r, 0)
        else:
            if self.is_me: path.addRoundedRect(0, 0, w - t, h, r, r)
            else: path.addRoundedRect(t, 0, w - t, h, r, r)
            
        painter.fillPath(path, QColor("#FEE500") if self.is_me else QColor("#FFFFFF"))

# 커스텀 텍스트 입력창
class CustomInput(QTextEdit):
    returnPressed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setPlaceholderText("Message...")
        self.setFrameShape(QFrame.NoFrame)
        font = self.font()
        font.setPixelSize(14)
        self.setFont(font)
        self.document().setDocumentMargin(0)
        self.setStyleSheet("""
            QTextEdit { 
                background-color: #FFFFFF; color: #000000;
                border-radius: 20px; padding: 10px 12px;
                border: 1px solid #BDC3C7;
            }
        """)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            self.returnPressed.emit()
        else:
            super().keyPressEvent(event)