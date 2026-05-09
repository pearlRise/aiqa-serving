import math
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QTextBrowser, QTextEdit
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QFont, QCursor, QPainter, QPainterPath, QColor, QTextOption

# 1.1 부드러운 스크롤 애니메이션 적용 영역
class SmoothScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.target_val = 0
        self.anim = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.setDuration(400)

    def wheelEvent(self, event):
        if not event.pixelDelta().isNull():
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

# 1.2 글래스모피즘 스타일의 반투명 프레임
class GlassFrame(QFrame):
    def __init__(self, radius=16, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            GlassFrame {{
                background-color: rgba(255, 255, 255, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.8);
                border-radius: {radius}px;
            }}
        """)

# 1.3 대시보드 내부 정보 표시용 셀
class IndicatorInfoCell(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("IndicatorInfoCell { background: transparent; border: none; border-radius: 0px; }")

# 1.4 아이콘 및 설명 포함 메뉴 아이템
class MenuListItem(GlassFrame):
    clicked = Signal(str)
    def __init__(self, icon, title, subtitle):
        super().__init__(radius=16)
        self.setFixedHeight(72)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        self.icon_label = QLabel(icon)
        self.icon_label.setFont(QFont("Apple Color Emoji", 24))
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent; border: none;")
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignVCenter)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #1A1A1A; font-size: 15px; font-weight: bold; background: transparent; border: none;")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet("color: #4A5568; font-size: 12px; background: transparent; border: none;")
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.subtitle_label)
        layout.addWidget(self.icon_label)
        layout.addLayout(text_layout)
        layout.addStretch()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.clicked.emit(self.title_label.text())
        super().mousePressEvent(event)

# 2.1 iMessage 스타일의 뾰족한 꼬리 말풍선 배경
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
        w, h, r, t = self.width(), self.height(), 16, 10
        if self.has_tail:
            if self.is_me:
                path.moveTo(r, 0); path.lineTo(w-r-t, 0); path.quadTo(w-t, 0, w-t, r)
                path.lineTo(w-t, h-14); path.cubicTo(w-t, h-8, w-t+4, h-2, w, h)
                path.quadTo(w-t+2, h, w-t-12, h); path.lineTo(r, h); path.quadTo(0, h, 0, h-r)
                path.lineTo(0, r); path.quadTo(0, 0, r, 0)
            else:
                path.moveTo(t+r, 0); path.lineTo(w-r, 0); path.quadTo(w, 0, w, r)
                path.lineTo(w, h-r); path.quadTo(w, h, w-r, h); path.lineTo(t+12, h)
                path.quadTo(t-2, h, 0, h); path.cubicTo(t-4, h-2, t, h-8, t, h-14)
                path.lineTo(t, r); path.quadTo(t, 0, t+r, 0)
        else:
            rect_w = w - t
            path.addRoundedRect(0 if self.is_me else t, 0, rect_w, h, r, r)
        painter.fillPath(path, QColor("#FEE500") if self.is_me else QColor("#FFFFFF"))

# 2.2 메시지, 발신자명, 시간 포함 채팅 블록
class ChatItem(QWidget):
    def __init__(self, text, is_me=False, sender_name="", is_consecutive=False):
        super().__init__()
        self.is_me, self.is_consecutive = is_me, is_consecutive
        self.main_layout = QVBoxLayout(self)
        self.top_margin = 4 if is_consecutive else 12
        self.main_layout.setContentsMargins(0, self.top_margin, 0, 0)
        self.main_layout.setSpacing(2)
        if not is_me and not is_consecutive and sender_name:
            self.name_label = QLabel(sender_name)
            self.name_label.setStyleSheet("color: #8E8E93; font-size: 11px; font-weight: bold; margin-left: 12px;")
            self.main_layout.addWidget(self.name_label)
        self.bubble_hlayout = QHBoxLayout()
        self.main_layout.addLayout(self.bubble_hlayout)
        self.bg_frame = BubbleFrame(is_me)
        self.bg_layout = QVBoxLayout(self.bg_frame)
        self.tail_width, self.padding_x, self.padding_y = 10, 12, 8
        self.bubble = QTextBrowser()
        self.bubble.setFrameShape(QFrame.NoFrame)
        self.bubble.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bubble.setStyleSheet("background: transparent; color: #000000;")
        font = self.bubble.font(); font.setPixelSize(13); self.bubble.setFont(font)
        self.doc = self.bubble.document(); self.doc.setDefaultFont(font); self.doc.setDocumentMargin(0)
        option = QTextOption(); option.setWrapMode(QTextOption.WrapAnywhere); self.doc.setDefaultTextOption(option)
        self.bubble.setPlainText(text); self.doc.setTextWidth(10000)
        self.pure_ideal_width = math.ceil(self.doc.idealWidth())
        self.bg_layout.addWidget(self.bubble)
        self.time_label = QLabel(datetime.now().strftime("%H:%M"))
        self.time_label.setStyleSheet("color: #556677; font-size: 10px;")
        if is_me:
            self.bubble_hlayout.addStretch()
            self.bubble_hlayout.addWidget(self.time_label, alignment=Qt.AlignBottom)
            self.bubble_hlayout.addWidget(self.bg_frame)
        else:
            self.bubble_hlayout.addWidget(self.bg_frame)
            self.bubble_hlayout.addWidget(self.time_label, alignment=Qt.AlignBottom)
            self.bubble_hlayout.addStretch()
        self.update_width(305)
    def update_width(self, window_width=305):
        max_text_width = int(window_width * 0.688) - (self.padding_x * 2) - self.tail_width
        actual_text_width = min(self.pure_ideal_width, max_text_width) + 2
        self.doc.setTextWidth(actual_text_width if self.pure_ideal_width > max_text_width else -1)
        text_height = math.ceil(self.doc.size().height()) + 2
        margin = (self.padding_x, self.padding_y, self.padding_x + self.tail_width, self.padding_y) if self.is_me else (self.padding_x + self.tail_width, self.padding_y, self.padding_x, self.padding_y)
        self.bg_layout.setContentsMargins(*margin)
        self.bubble.setFixedSize(actual_text_width, text_height)
        self.bg_frame.setFixedSize(actual_text_width + (self.padding_x * 2) + self.tail_width, text_height + (self.padding_y * 2))
        self.setFixedHeight(self.main_layout.sizeHint().height())
    def remove_tail_and_time(self):
        self.bg_frame.has_tail = False; self.bg_frame.update(); self.time_label.hide()

# 2.3 엔터 키 전송 및 자동 높이 조절 입력창
class CustomInput(QTextEdit):
    returnPressed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40); self.setPlaceholderText("Message...")
        self.setFrameShape(QFrame.NoFrame)
        font = self.font(); font.setPixelSize(14); self.setFont(font)
        self.setStyleSheet("""
            QTextEdit { 
                background-color: #FFFFFF; color: #000000;
                border-radius: 20px; padding: 10px 12px; border: 1px solid #BDC3C7;
            }
            QScrollBar:vertical { border: none; background: transparent; width: 4px; }
            QScrollBar::handle:vertical { background: rgba(0, 0, 0, 0.1); border-radius: 2px; }
        """)
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            self.returnPressed.emit()
        else: super().keyPressEvent(event)