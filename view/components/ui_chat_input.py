from PySide6.QtWidgets import QTextEdit, QFrame
from PySide6.QtCore import Qt, Signal
from view.configuration.app_texts import CHAT_PLACEHOLDER

class CustomInput(QTextEdit):
    returnPressed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document().setDocumentMargin(0); self.setFixedHeight(44); self.setPlaceholderText(CHAT_PLACEHOLDER)
        self.setFrameShape(QFrame.NoFrame); self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        font = self.font(); font.setPixelSize(14); self.setFont(font)
        self.setStyleSheet("QTextEdit { background-color: #FFFFFF; color: #000000; border-radius: 22px; padding: 12px 12px; border: 1px solid #BDC3C7; } QScrollBar:vertical { border: none; background: transparent; width: 4px; } QScrollBar::handle:vertical { background: rgba(0, 0, 0, 0.3); border-radius: 2px; } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; background: none; } QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }")
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier): self.returnPressed.emit()
        else: super().keyPressEvent(event)