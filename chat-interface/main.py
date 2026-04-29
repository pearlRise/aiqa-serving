# 1. 라이브러리 임포트
import sys
import math
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QScrollArea, QLabel, QFrame, 
    QGraphicsOpacityEffect, QTextBrowser, QTextEdit, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Signal
from PySide6.QtGui import QTextOption, QPainter, QPainterPath, QColor

# 2. 커스텀 UI 컴포넌트
# 2.1. 말풍선 껍데기 (iMessage 스타일 꼬리 프레임)
class BubbleFrame(QFrame):
    def __init__(self, is_me):
        super().__init__()
        self.is_me = is_me
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        
        w = self.width()
        h = self.height()
        r = 15  # 모서리 곡률
        t = 8   # 꼬리 너비

        if self.is_me:
            # 2.1.1. 내 말풍선 (우측 하단 꼬리)
            path.moveTo(r, 0)
            path.lineTo(w - r - t, 0)
            path.quadTo(w - t, 0, w - t, r)
            path.lineTo(w - t, h - r - 5)
            path.quadTo(w - t, h - 5, w, h)
            path.quadTo(w - t - 2, h - 2, w - t - 8, h - 8)
            path.lineTo(r, h - 8)
            path.quadTo(0, h - 8, 0, h - 8 - r)
            path.lineTo(0, r)
            path.quadTo(0, 0, r, 0)
        else:
            # 2.1.2. 상대방 말풍선 (좌측 하단 꼬리)
            path.moveTo(r + t, 0)
            path.lineTo(w - r, 0)
            path.quadTo(w, 0, w, r)
            path.lineTo(w, h - r - 8)
            path.quadTo(w, h - 8, w - r, h - 8)
            path.lineTo(r + t + 8, h - 8)
            path.quadTo(t + 2, h - 2, 0, h)
            path.quadTo(t, h - 5, t, h - r - 5)
            path.lineTo(t, r)
            path.quadTo(t, 0, r + t, 0)
            
        painter.fillPath(path, QColor("#FEE500") if self.is_me else QColor("#FFFFFF"))

# 2.2. 개별 채팅 메시지 블록
class ChatItem(QWidget):
    def __init__(self, text, is_me=False):
        super().__init__()
        self.is_me = is_me
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0) # 불필요한 외부 마진 제거
        
        self.bg_frame = BubbleFrame(is_me)
        self.bg_layout = QVBoxLayout(self.bg_frame)
        self.tail_width = 8
        self.padding_x = 12
        self.padding_y = 8 # 7 -> 8px로 정렬
        
        # 2.2.1. 비대칭 마진 설정 (꼬리 침범 방지)
        if is_me:
            margin = (self.padding_x, self.padding_y, self.padding_x + self.tail_width, self.padding_y + 8)
        else:
            margin = (self.padding_x + self.tail_width, self.padding_y, self.padding_x, self.padding_y + 8)
        self.bg_layout.setContentsMargins(*margin)
        
        # 2.2.2. 텍스트 엔진 및 스타일 설정
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
        
        # 2.2.3. 순수 텍스트 너비 1차 측정
        self.doc.setTextWidth(10000)
        self.pure_ideal_width = math.ceil(self.doc.idealWidth())
        
        self.bg_layout.addWidget(self.bubble)
        self.time_label = QLabel(datetime.now().strftime("%H:%M"))
        self.time_label.setStyleSheet("color: #556677; font-size: 10px;")
        
        # 2.2.4. 발신자에 따른 위젯 조립
        if is_me:
            self.layout.addStretch()
            self.layout.addWidget(self.time_label, alignment=Qt.AlignBottom)
            self.layout.addWidget(self.bg_frame)
        else:
            self.layout.addWidget(self.bg_frame)
            self.layout.addWidget(self.time_label, alignment=Qt.AlignBottom)
            self.layout.addStretch()
            
        self.update_width(305)

    def update_width(self, window_width):
        # 2.2.5. 동적 크기 재계산 로직
        max_text_width = int(window_width * 0.688) - (self.padding_x * 2) - self.tail_width
        actual_text_width = min(self.pure_ideal_width, max_text_width) + 2
        
        self.doc.setTextWidth(actual_text_width if self.pure_ideal_width > max_text_width else -1)
        text_height = math.ceil(self.doc.size().height()) + 2
        
        self.bubble.setFixedSize(actual_text_width, text_height)
        self.bg_frame.setFixedSize(actual_text_width + (self.padding_x * 2) + self.tail_width, text_height + (self.padding_y * 2) + 8)
        self.setFixedHeight(self.bg_frame.height()) # 외부 마진(10) 제거 후 프레임 높이에 딱 맞춤

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

        # 2.3.1. 스크롤바 우측 밀착 스타일링
        self.setStyleSheet("""
            QTextEdit { 
                background-color: #FFFFFF; color: #000000;
                border-radius: 20px; 
                padding: 10px 12px; /* 상하 10px 패딩으로 수직 중앙 정렬 완벽 통제 */
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
        # 2.3.2. 엔터 전송 및 Shift+Enter 줄바꿈 처리
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            self.returnPressed.emit()
        else:
            super().keyPressEvent(event)

# 3. 메인 인터페이스
class ChatInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        # 3.1. 기본 윈도우 설정
        self.setMinimumSize(305, 655)
        self.resize(305, 655)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.container = QWidget()
        self.container.setObjectName("MainBody")
        self.setCentralWidget(self.container)
        self.container.setStyleSheet("#MainBody { background-color: #ABC1D1; border: 1px solid #222; border-radius: 48px; }")
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 10) # 전체 외부 마진 0으로 초기화
        self.main_layout.setSpacing(0) # 컴포넌트 간 기본 간격 0
        
        # 3.2. 상단 아일랜드 장식 (상단 마진 명시적 추가)
        self.main_layout.addSpacing(16)
        self.island = QFrame()
        self.island.setFixedSize(120, 26)
        self.island.setStyleSheet("background-color: black; border-radius: 13px;")
        self.main_layout.addWidget(self.island, alignment=Qt.AlignHCenter)
        
        # 3.3. 채팅 스크롤 영역 (Stretch Factor 1)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
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

        self.scroll.verticalScrollBar().rangeChanged.connect(self.scroll_to_bottom)
        
        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(16, 16, 8, 16) # 좌/상/우/하 마진 체계화
        self.chat_layout.setSpacing(12) # [수정] 말풍선 간의 간격 12px 통일
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.chat_content)
        self.main_layout.addWidget(self.scroll, 1)

        # 3.4. 하단 입력 영역 (Stretch Factor 0)
        self.input_container = QWidget()
        self.input_layout = QHBoxLayout(self.input_container)
        self.input_layout.setContentsMargins(16, 8, 16, 16) # 하단/좌우 16px, 상단 8px
        self.input_layout.setSpacing(8) # 버튼과 입력창 사이 8px
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
        
        # 3.5. 리사이즈 및 드래그 상태 변수
        self.resizing = False
        self.resize_margin = 10
        self.old_pos = None

    # 4. 핵심 비즈니스 로직
    def send_message(self):
        # 4.1. 메시지 전송 및 입력창 초기화
        text = self.input_field.toPlainText().strip()
        if not text:
            return
            
        self.add_chat_bubble(text, is_me=True)
        self.input_field.clear()
        self.input_field.setFixedHeight(40)
        
        # 4.2. 테스트용 에코 봇 응답 (0.5초 지연)
        QTimer.singleShot(500, lambda: self.add_chat_bubble(f"에코: {text}", is_me=False))

    def add_chat_bubble(self, text, is_me):
        # 4.3. 말풍선 생성 및 레이아웃 배치
        bubble = ChatItem(text, is_me)
        bubble.update_width(self.width())
        self.chat_layout.addWidget(bubble)
        QTimer.singleShot(10, self.scroll_to_bottom)

    def adjust_input_height(self):
        # 4.4. 내용 길이에 따른 유동적 입력창 높이 조절
        doc = self.input_field.document()
        doc_height = doc.size().height()
        
        # 내부 마진이 없으므로 1줄은 확실하게 22px 이하임. 이때는 40px로 락(Lock)
        if doc_height <= 22:
            new_height = 40
        else:
            # 두 줄부터: 실제 높이 + 상하 패딩(20px) + 상하 테두리(2px) 보정
            new_height = max(40, min(120, int(doc_height) + 22))
            
        if self.input_field.height() != new_height:
            self.input_field.setFixedHeight(new_height)
            QTimer.singleShot(0, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        # 4.5. 자동 스크롤 추적
        scrollbar = self.scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # 5. 프레임리스 윈도우 이벤트 핸들러
    def resizeEvent(self, event):
        # 5.1. 창 크기 조절 시 반응형 말풍선 갱신
        super().resizeEvent(event)
        for i in range(self.chat_layout.count()):
            widget = self.chat_layout.itemAt(i).widget()
            if isinstance(widget, ChatItem):
                widget.update_width(self.width())

    def mousePressEvent(self, event):
        # 5.2. 드래그 vs 리사이즈 모드 판별
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            if pos.x() > self.width() - self.resize_margin or pos.y() > self.height() - self.resize_margin:
                self.resizing = True
            else:
                self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        # 5.3. 마우스 커서 변경 및 창 조절/이동 수행
        pos = event.position().toPoint()
        
        is_right = pos.x() > self.width() - self.resize_margin
        is_bottom = pos.y() > self.height() - self.resize_margin
        
        if is_right and is_bottom:
            self.setCursor(Qt.SizeFDiagCursor)
        elif is_right:
            self.setCursor(Qt.SizeHorCursor)
        elif is_bottom:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            
        if self.resizing:
            self.resize(max(self.minimumWidth(), pos.x()), max(self.minimumHeight(), pos.y()))
        elif self.old_pos:
            curr = event.globalPosition().toPoint()
            self.move(self.pos() + curr - self.old_pos)
            self.old_pos = curr

    def mouseReleaseEvent(self, event):
        # 5.4. 이벤트 상태 초기화
        self.resizing = False
        self.old_pos = None

# 6. 애플리케이션 진입점
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatInterface()
    window.show()
    sys.exit(app.exec())