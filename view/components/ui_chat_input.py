#============================================================
# - subject: ui_chat_input.py
# - created: 2026-05-12
# - updated: 2026-05-14
# - summary: Custom text input field for chat interactions.
# - caution: Captures Enter key for submission without shift.
#============================================================
from PySide6.QtWidgets import QTextEdit, QFrame
from PySide6.QtCore import Qt, Signal
from data.view.app_texts import CHAT_PLACEHOLDER

# Shift 미포함 Enter 입력 시 전송 이벤트를 발생시키는 커스텀 텍스트박스
class CustomInput(QTextEdit):
    returnPressed = Signal()
    # 플레이스홀더, 스타일 및 레이아웃 마진 초기화
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document().setDocumentMargin(0); self.setFixedHeight(44); self.setPlaceholderText(CHAT_PLACEHOLDER)
        self.setFrameShape(QFrame.NoFrame); self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        font = self.font(); font.setPixelSize(14); self.setFont(font)
        self.setStyleSheet("QTextEdit { background-color: #FFFFFF; color: #000000; border-radius: 22px; padding: 12px 12px; border: 1px solid #BDC3C7; } QScrollBar:vertical { border: none; background: transparent; width: 4px; } QScrollBar::handle:vertical { background: rgba(0, 0, 0, 0.3); border-radius: 2px; } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; background: none; } QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }")
    # 키보드 입력 가로채어 Shift 없이 Enter 시 returnPressed 시그널 방출
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier): self.returnPressed.emit()
        else: super().keyPressEvent(event)