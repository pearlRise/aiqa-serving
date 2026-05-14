#============================================================
# - subject: ui_chat_bubble.py
# - created: 2026-05-12
# - updated: 2026-05-14
# - summary: Renders dynamic chat message bubbles and text.
# - caution: Word wrapping logic needs careful sizing.
#============================================================
import math
from datetime import datetime
from PySide6.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPainterPath, QColor, QTextOption
from view.components.ui_marquee_label import MarqueeLabel

# 발신자, 수신자에 맞게 꼬리가 달린 말풍선 벡터 도형 렌더링 프레임
class BubbleFrame(QFrame):
    def __init__(self, is_me):
        super().__init__()
        self.is_me, self.has_tail = is_me, True
        self.setAttribute(Qt.WA_TranslucentBackground)
        
    # QPainterPath를 사용해 둥근 말풍선 외곽선과 꼬리 좌표 그리기
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
            path.addRoundedRect(0 if self.is_me else t, 0, w - t, h, r, r)
        painter.fillPath(path, QColor("#FEE500") if self.is_me else QColor("#FFFFFF"))

# 발신자 텍스트와 시간, 말풍선 백그라운드를 포함하는 메시지 전체 컨테이너
class ChatItem(QWidget):
    # 텍스트 높이 및 넓이 초기 측정 후 컴포넌트 배치
    def __init__(self, text, is_me=False, sender_name="", is_consecutive=False):
        super().__init__()
        self.is_me, self.is_consecutive = is_me, is_consecutive
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 4 if is_consecutive else 12, 0, 0)
        self.main_layout.setSpacing(2)
        if not is_me and not is_consecutive and sender_name:
            self.name_label = MarqueeLabel(sender_name)
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
        self.bubble.setPlainText(text); self.doc.setTextWidth(-1)
        # 자동 줄바꿈 전 순수 한 줄 텍스트 너비 저장
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
        self.needs_width_update = False
        
    # 윈도우 크기에 맞춰 말풍선의 텍스트 WordWrap 및 패딩 갱신
    def update_width(self, window_width=305):
        max_text_width = int(window_width * 0.688) - (self.padding_x * 2) - self.tail_width
        actual_text_width = min(self.pure_ideal_width, max_text_width) + 2
        self.doc.setTextWidth(actual_text_width if self.pure_ideal_width > max_text_width else -1)
        text_height = math.ceil(self.doc.size().height()) + 4
        margin = (self.padding_x, self.padding_y, self.padding_x + self.tail_width, self.padding_y) if self.is_me else (self.padding_x + self.tail_width, self.padding_y, self.padding_x, self.padding_y)
        self.bg_layout.setContentsMargins(*margin)
        self.bubble.setFixedSize(actual_text_width, text_height)
        self.bg_frame.setFixedSize(actual_text_width + (self.padding_x * 2) + self.tail_width, text_height + (self.padding_y * 2))
        if hasattr(self, 'name_label'):
            self.name_label.setMaximumWidth(int(window_width * 0.688))
        self.setFixedHeight(self.main_layout.sizeHint().height())
        
    # 연속 메시지 시 이전 메시지의 꼬리와 시간 숨김 처리
    def remove_tail_and_time(self): self.bg_frame.has_tail = False; self.bg_frame.update(); self.time_label.hide()
    
    # 스트리밍 시 텍스트 갱신 및 폭 재계산
    def update_text(self, text): self.bubble.setPlainText(text); self.doc.setTextWidth(-1); self.pure_ideal_width = math.ceil(self.doc.idealWidth())