# 1. 라이브러리 임포트
import sys
import math
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QScrollArea, QLabel, QFrame, 
    QGraphicsOpacityEffect, QTextBrowser, QTextEdit
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Signal
from PySide6.QtGui import QTextOption, QPainter, QPainterPath, QColor

# 2. 커스텀 UI 컴포넌트
# 2.1. 말풍선 배경 프레임 (iMessage 스타일 뾰족 꼬리)
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
        
        w = self.width()
        h = self.height()
        r = 16  # 모서리 곡률
        t = 10  # 꼬리가 밖으로 나가는 너비

        if self.has_tail:
            if self.is_me:
                # 2.1.1. 내 말풍선 (우측 뾰족 꼬리)
                path.moveTo(r, 0)
                path.lineTo(w - r - t, 0)
                path.quadTo(w - t, 0, w - t, r)
                path.lineTo(w - t, h - 14)
                # 밖으로 뾰족하게 튀어나가는 곡선
                path.cubicTo(w - t, h - 8, w - t + 4, h - 2, w, h)
                # 안으로 파고드는 오목한 곡선 (iMessage 핵심 디테일)
                path.quadTo(w - t + 2, h, w - t - 12, h)
                path.lineTo(r, h)
                path.quadTo(0, h, 0, h - r)
                path.lineTo(0, r)
                path.quadTo(0, 0, r, 0)
            else:
                # 2.1.2. 상대방 말풍선 (좌측 뾰족 꼬리)
                path.moveTo(t + r, 0)
                path.lineTo(w - r, 0)
                path.quadTo(w, 0, w, r)
                path.lineTo(w, h - r)
                path.quadTo(w, h, w - r, h)
                path.lineTo(t + 12, h)
                # 안으로 파고드는 오목한 곡선
                path.quadTo(t - 2, h, 0, h)
                # 위로 뾰족하게 말아올리는 곡선
                path.cubicTo(t - 4, h - 2, t, h - 8, t, h - 14)
                path.lineTo(t, r)
                path.quadTo(t, 0, t + r, 0)
        else:
            # 2.1.3. 꼬리 없는 연속 메시지
            if self.is_me:
                path.addRoundedRect(0, 0, w - t, h, r, r)
            else:
                path.addRoundedRect(t, 0, w - t, h, r, r)
            
        painter.fillPath(path, QColor("#FEE500") if self.is_me else QColor("#FFFFFF"))

# 2.2. 개별 채팅 메시지 블록 (데이터 및 레이아웃 조립)
class ChatItem(QWidget):
    def __init__(self, text, is_me=False, sender_name="", is_consecutive=False):
        super().__init__()
        self.is_me = is_me
        self.is_consecutive = is_consecutive
        self.has_tail = True
        self.last_window_width = 305
        self.needs_width_update = False
        
        self.main_layout = QVBoxLayout(self)
        self.top_margin = 4 if is_consecutive else 12
        self.main_layout.setContentsMargins(0, self.top_margin, 0, 0)
        self.main_layout.setSpacing(2)

        self.has_name_label = not is_me and not is_consecutive and sender_name
        
        if self.has_name_label:
            self.name_label = QLabel(sender_name)
            self.name_label.setStyleSheet("color: #8E8E93; font-size: 11px; font-weight: bold;")
            self.name_label.setContentsMargins(12, 0, 0, 0)
            self.main_layout.addWidget(self.name_label)

        self.bubble_hlayout = QHBoxLayout()
        self.bubble_hlayout.setSpacing(0)
        self.bubble_hlayout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.bubble_hlayout)
        
        self.bg_frame = BubbleFrame(is_me)
        self.bg_layout = QVBoxLayout(self.bg_frame)
        self.tail_width = 10
        self.padding_x = 12
        self.padding_y = 8
        
        self.bubble = QTextBrowser()
        self.bubble.setFrameShape(QFrame.NoFrame)
        self.bubble.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bubble.setStyleSheet("background: transparent; color: #000000;")
        
        font = self.bubble.font()
        font.setPixelSize(13)
        self.bubble.setFont(font)
        
        self.doc = self.bubble.document()
        self.doc.setDefaultFont(font)
        self.doc.setDocumentMargin(0)
        
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapAnywhere)
        self.doc.setDefaultTextOption(option)
        self.bubble.setPlainText(text)
        
        self.doc.setTextWidth(10000)
        self.pure_ideal_width = math.ceil(self.doc.idealWidth())
        
        self.bg_layout.addWidget(self.bubble)
        self.time_label = QLabel(datetime.now().strftime("%H:%M"))
        self.time_label.setStyleSheet("color: #556677; font-size: 10px;")
        
        if is_me:
            self.bubble_hlayout.addStretch()
            self.time_label.setContentsMargins(0, 0, 5, 8) 
            self.bubble_hlayout.addWidget(self.time_label, alignment=Qt.AlignBottom)
            self.bubble_hlayout.addWidget(self.bg_frame)
        else:
            self.bubble_hlayout.addWidget(self.bg_frame)
            self.time_label.setContentsMargins(5, 0, 0, 8)
            self.bubble_hlayout.addWidget(self.time_label, alignment=Qt.AlignBottom)
            self.bubble_hlayout.addStretch()
            
        self.update_width(305)
        self.needs_width_update = False # [신규] 리사이즈 필요 여부 플래그

    def update_width(self, window_width=None):
        if window_width is not None:
            self.last_window_width = window_width
        window_width = self.last_window_width
        
        max_text_width = int(window_width * 0.688) - (self.padding_x * 2) - self.tail_width
        actual_text_width = min(self.pure_ideal_width, max_text_width) + 2
        
        self.doc.setTextWidth(actual_text_width if self.pure_ideal_width > max_text_width else -1)
        text_height = math.ceil(self.doc.size().height()) + 2
        
        # [수정] iMessage 꼬리는 수평으로 펼쳐지므로 수직 마진을 변화시킬 필요가 없음 (뚱뚱함 해결)
        if self.is_me:
            margin = (self.padding_x, self.padding_y, self.padding_x + self.tail_width, self.padding_y)
        else:
            margin = (self.padding_x + self.tail_width, self.padding_y, self.padding_x, self.padding_y)
        self.bg_layout.setContentsMargins(*margin)
        
        self.bubble.setFixedSize(actual_text_width, text_height)
        self.bg_frame.setFixedSize(actual_text_width + (self.padding_x * 2) + self.tail_width, text_height + (self.padding_y * 2))
        
        total_h = self.top_margin + self.bg_frame.height()
        if self.has_name_label:
            total_h += self.name_label.sizeHint().height() + self.main_layout.spacing()
        self.setFixedHeight(total_h)

    def remove_tail_and_time(self):
        self.has_tail = False
        self.bg_frame.has_tail = False
        self.bg_frame.update()
        self.time_label.hide()
        self.update_width()

# 2.3. 하단 유동 입력창
class CustomInput(QTextEdit):
    returnPressed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setPlaceholderText("Message...")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.NoFrame)
        
        font = self.font()
        font.setPixelSize(14)
        self.setFont(font)
        self.document().setDocumentMargin(0)

        self.setStyleSheet("""
            QTextEdit { 
                background-color: #FFFFFF; color: #000000;
                border-radius: 20px; 
                padding: 10px 12px;
                border: 1px solid #BDC3C7;
            }
            QScrollBar:vertical {
                border: none; background: transparent; width: 4px; margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.1); border-radius: 2px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                height: 0px; background: none;
            }
        """)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            self.returnPressed.emit()
        else:
            super().keyPressEvent(event)

# 3. 메인 인터페이스
class ChatView(QWidget):
    def __init__(self):
        super().__init__()
        
        # 3.1. 윈도우 및 메인 컨테이너 설정
        self.container = QWidget()
        self.container.setObjectName("MainBody")

        # 자신(self)의 바탕 레이아웃을 만들고 컨테이너를 꽉 채워 넣음
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)
        base_layout.addWidget(self.container)
        
        self.container.setStyleSheet("#MainBody { background-color: #ABC1D1; border: 1px solid #222; border-radius: 48px; }")        
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 10)
        self.main_layout.setSpacing(0) 
        self.main_layout.addSpacing(21)

        # 3.2. 채팅 스크롤 영역 설정 (이제 전체 화면을 차지함)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.verticalScrollBar().setSingleStep(25)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none; background: transparent; width: 8px; margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.15); border-radius: 4px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: rgba(0, 0, 0, 0.3); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                height: 0px; background: none;
            }
        """)

        # 스크롤바 페이드 효과 처리
        self.scroll_effect = QGraphicsOpacityEffect(self.scroll.verticalScrollBar())
        self.scroll.verticalScrollBar().setGraphicsEffect(self.scroll_effect)
        self.scroll_effect.setOpacity(0.0)
        
        self.scroll_timer = QTimer(self)
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self.hide_scrollbar)
        self.scrollbar_anim = None
        
        self.scroll.verticalScrollBar().valueChanged.connect(self.show_scrollbar)
        self.scroll.verticalScrollBar().rangeChanged.connect(self.show_scrollbar)
        
        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(16, 30, 8, 16)
        self.chat_layout.setSpacing(0) 
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.chat_content)
        self.main_layout.addWidget(self.scroll, 1)

        # [신규] 리사이즈 연산 부하를 줄이기 위한 디바운싱 타이머
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.update_visible_bubbles)
        self.last_width = self.width()

        # [신규] 스크롤을 내릴 때 화면에 새로 들어오는 말풍선 업데이트
        self.scroll.verticalScrollBar().valueChanged.connect(self.update_visible_bubbles)

        # 3.3. 하단 입력 영역 설정
        self.input_container = QWidget()
        self.input_layout = QHBoxLayout(self.input_container)
        self.input_layout.setContentsMargins(16, 8, 16, 16)
        self.input_layout.setSpacing(8)
        self.input_layout.setAlignment(Qt.AlignBottom)
        
        self.input_field = CustomInput()
        self.input_field.textChanged.connect(self.adjust_input_height)
        self.input_field.returnPressed.connect(self.send_message)
        
        self.send_btn = QPushButton("↑")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setStyleSheet("""
            QPushButton { 
                background-color: #007AFF; color: white; 
                border-radius: 20px;
                font-weight: bold; font-size: 16px; border: none; 
            }
            QPushButton:pressed { background-color: #0051A8; }
        """)
        self.send_btn.clicked.connect(self.send_message)
        
        self.input_layout.addWidget(self.input_field)
        self.input_layout.addWidget(self.send_btn)
        self.main_layout.addWidget(self.input_container, 0)

        # 3.5. 대화 그룹화 상태 추적 변수
        self.last_sender_id = None
        self.last_chat_item = None

        # 3.6. 진입 시 포커스 부여
        self.input_field.setFocus()

    # 4. 기능 및 이벤트 로직
    # 4.1. 스크롤바 제어 로직
    def show_scrollbar(self, *args):
        self.scroll_effect.setOpacity(1.0)
        self.scroll_timer.start(1500)

    def hide_scrollbar(self):
        self.scrollbar_anim = QPropertyAnimation(self.scroll_effect, b"opacity")
        self.scrollbar_anim.setDuration(300)
        self.scrollbar_anim.setStartValue(1.0)
        self.scrollbar_anim.setEndValue(0.0)
        self.scrollbar_anim.start()

    # 4.2. 메시지 전송 및 렌더링
    def send_message(self):
        text = self.input_field.toPlainText().strip()
        if not text:
            return
            
        self.add_chat_bubble(text, is_me=True)
        self.input_field.clear()
        self.input_field.setFixedHeight(40)
        
        QTimer.singleShot(500, self, lambda: self.add_chat_bubble(f"에코: {text}", is_me=False, sender_name="Ollama Bot"))
        QTimer.singleShot(1000, self, lambda: self.add_chat_bubble("추가 답변입니다.", is_me=False, sender_name="Ollama Bot"))

    def add_chat_bubble(self, text, is_me, sender_name=""):
        current_sender_id = "ME" if is_me else sender_name
        is_consecutive = (self.last_sender_id == current_sender_id)

        if is_consecutive and self.last_chat_item:
            self.last_chat_item.remove_tail_and_time()

        bubble = ChatItem(text, is_me=is_me, sender_name=sender_name, is_consecutive=is_consecutive)
        bubble.update_width(self.width())
        self.chat_layout.addWidget(bubble)
        
        self.last_sender_id = current_sender_id
        self.last_chat_item = bubble
        
        QTimer.singleShot(10, self.scroll_to_bottom)

    # 4.3. 입력창 동적 크기 조절
    def adjust_input_height(self):
        doc = self.input_field.document()
        doc_height = doc.size().height()
        
        if doc_height <= 22:
            new_height = 40
        else:
            new_height = max(40, min(120, int(doc_height) + 22))
            
        if self.input_field.height() != new_height:
            self.input_field.setFixedHeight(new_height)
            QTimer.singleShot(0, self.scroll_to_bottom)

    # 4.4. 화면 최하단 스크롤 추적
    def scroll_to_bottom(self):
        scrollbar = self.scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    # 4.5. 화면 리사이즈 시 말풍선 너비 반응형 처리 (최적화 버전)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # 너비가 실제로 변했을 때만 연산 준비
        if self.width() != self.last_width:
            self.last_width = self.width()
            
            # 모든 채팅 위젯에 '계산 필요함' 꼬리표 부착 (단순 변수 변경이라 부하 없음)
            for i in range(self.chat_layout.count()):
                item = self.chat_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, ChatItem):
                        widget.needs_width_update = True
            
            # 창 드래그 중에는 연산을 미루고, 드래그가 멈추면(100ms 후) 한 번만 렌더링 실행
            self.resize_timer.start(100)
            
            # 창 드래그 중에는 연산을 미루고, 드래그가 멈추면(1ms 후) 한 번만 렌더링 실행
            self.resize_timer.start(1)

    # 4.6. 현재 화면(뷰포트)에 보이는 말풍선만 선택적 렌더링
    def update_visible_bubbles(self):
        scroll_y = self.scroll.verticalScrollBar().value()
        viewport_height = self.scroll.viewport().height()
        
        # 스크롤 영역 위아래로 약간의 여유 공간(버퍼)을 두어 렌더링
        buffer = 150 
        visible_top = scroll_y - buffer
        visible_bottom = scroll_y + viewport_height + buffer

        for i in range(self.chat_layout.count()):
            item = self.chat_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, ChatItem) and widget.needs_width_update:
                    # 위젯의 Y 좌표가 가시 영역 내에 있는지 수학적 판별
                    widget_y = widget.pos().y()
                    if visible_top <= widget_y <= visible_bottom:
                        widget.update_width(self.width())
                        widget.needs_width_update = False # 렌더링 완료 꼬리표 떼기 