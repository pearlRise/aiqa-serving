import sys
import math
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QScrollArea, QLabel, QFrame, 
    QGraphicsOpacityEffect, QTextBrowser
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation
from PySide6.QtGui import QTextOption

class ChatItem(QWidget):
    """말풍선 개별 위젯: 배경 프레임과 텍스트 브라우저를 분리하여 레이아웃 충돌 방지"""
    def __init__(self, text, is_me=False):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)
        self.layout.setSpacing(5)

        # 1. 배경 프레임 설정 (둥근 모서리 및 배경색 담당)
        self.bg_frame = QFrame()
        bg_color = "#FEE500" if is_me else "#FFFFFF"
        self.bg_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 12px;
            }}
        """)
        
        # 내부 레이아웃을 통해 CSS 패딩 효과를 물리적으로 구현 (계산 오차 방지)
        self.bg_layout = QVBoxLayout(self.bg_frame)
        padding_x = 12
        padding_y = 7
        self.bg_layout.setContentsMargins(padding_x, padding_y, padding_x, padding_y)
        self.bg_layout.setSpacing(0)

        # 2. 텍스트 브라우저 설정 (실제 내용 및 줄바꿈 담당)
        self.bubble = QTextBrowser()
        self.bubble.setFrameShape(QFrame.NoFrame)
        self.bubble.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bubble.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bubble.setStyleSheet("background: transparent; color: #000000;")
        
        # 폰트 및 문서 엔진 설정 (렌더링 폰트와 계산용 폰트를 일치시킴)
        font = self.bubble.font()
        font.setPixelSize(13)
        self.bubble.setFont(font)
        
        doc = self.bubble.document()
        doc.setDefaultFont(font)
        doc.setDocumentMargin(0) 
        
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapAnywhere) # 공백 없는 문자열도 강제 개행
        doc.setDefaultTextOption(option)
        
        self.bubble.setPlainText(text)
        
        # 3. 크기 동적 계산 로직
        max_bubble_width = 210
        max_text_width = max_bubble_width - (padding_x * 2) 
        doc.setTextWidth(max_text_width) # 엔진에 최대 너비를 주입하여 높이 계산 유도
        
        # 텍스트 너비와 높이를 픽셀 단위로 정밀 측정 (소수점 올림 처리)
        text_width = math.ceil(doc.idealWidth()) + 2
        actual_text_width = min(text_width, max_text_width)
        text_height = math.ceil(doc.size().height()) + 2
        
        # 브라우저와 프레임의 크기를 고정하여 레이아웃 팽창 버그 차단
        self.bubble.setFixedSize(actual_text_width, text_height)
        self.bg_layout.addWidget(self.bubble)

        frame_width = actual_text_width + (padding_x * 2)
        frame_height = text_height + (padding_y * 2)
        self.bg_frame.setFixedSize(frame_width, frame_height)
        
        # 부모 위젯의 높이를 고정하여 리스트에서 균등 분할되는 현상 방지
        self.setFixedHeight(frame_height + 10)

        # 4. 시간 표시 라벨
        curr_time = datetime.now().strftime("%H:%M")
        self.time_label = QLabel(curr_time)
        self.time_label.setStyleSheet("color: #556677; font-size: 10px;")
        
        if is_me:
            self.layout.addStretch()
            self.layout.addWidget(self.time_label, alignment=Qt.AlignBottom)
            self.layout.addWidget(self.bg_frame)
        else:
            self.layout.addWidget(self.bg_frame)
            self.layout.addWidget(self.time_label, alignment=Qt.AlignBottom)
            self.layout.addStretch()


class ChatInterface(QMainWindow):
    """메인 윈도우: 아이폰 스타일의 프레임리스 인터페이스 구현"""
    def __init__(self):
        super().__init__()
        
        self.setFixedSize(305, 655) 
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 배경 컨테이너 (둥근 모서리 적용)
        self.container = QWidget()
        self.container.setObjectName("MainBody") 
        self.setCentralWidget(self.container)
        self.container.setStyleSheet("""
            #MainBody { 
                background-color: #ABC1D1; 
                border: 1px solid #222; 
                border-radius: 48px; 
            }
        """)

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 15) 
        self.main_layout.setSpacing(10)

        # 상단 다이내믹 아일랜드 디자인 요소
        self.main_layout.addSpacing(15) 
        self.island = QFrame()
        self.island.setFixedSize(120, 26) 
        self.island.setStyleSheet("background-color: black; border-radius: 13px;")
        self.main_layout.addWidget(self.island, alignment=Qt.AlignHCenter)
        
        # 스크롤 영역 설정 (스크롤바 디자인 커스텀 포함)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn) 
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollArea > QWidget > QWidget { border: none; background: transparent; }
            QScrollArea::viewport { border: none; background: transparent; }
            QScrollBar:vertical { border: none; background: transparent; width: 8px; }                      
            QScrollBar::handle:vertical { background: rgba(0, 0, 0, 0.2); min-height: 30px; border-radius: 4px; }
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)
        
        # 스크롤바 페이드 애니메이션 설정
        self.scrollbar_effect = QGraphicsOpacityEffect()
        self.scroll.verticalScrollBar().setGraphicsEffect(self.scrollbar_effect)
        self.fade_anim = QPropertyAnimation(self.scrollbar_effect, b"opacity")
        self.fade_anim.setDuration(300) 
        
        self.fade_timer = QTimer()
        self.fade_timer.setInterval(1500) 
        self.fade_timer.setSingleShot(True)
        self.fade_timer.timeout.connect(self.fade_out_scrollbar)

        self.scroll.verticalScrollBar().valueChanged.connect(self.wake_scrollbar)
        self.scroll.verticalScrollBar().rangeChanged.connect(self.handle_range_changed)
        
        # 채팅 메시지 적재 레이아웃
        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent; border: none;")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(15, 10, 7, 10) 
        self.chat_layout.setAlignment(Qt.AlignTop) # 메시지를 상단부터 정렬
        
        self.scroll.setWidget(self.chat_content)
        self.main_layout.addWidget(self.scroll)
        
        # 하단 메시지 입력 바
        self.input_container = QWidget()
        self.input_container.setFixedHeight(50) 
        input_layout = QHBoxLayout(self.input_container)
        input_layout.setContentsMargins(15, 0, 15, 10) 
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Let's have a conversation!")
        self.input_field.setFixedHeight(32)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #BDC3C7;
                border-radius: 16px;
                padding: 0 12px;
                font-size: 14px;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton("↑")
        self.send_btn.setFixedSize(32, 32)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF; color: white; 
                border-radius: 16px; font-weight: bold; font-size: 16px;
            }
            QPushButton:pressed { background-color: #0051A8; }
        """)
        self.send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        self.main_layout.addWidget(self.input_container)

        self.old_pos = None

    # 마우스 드래그를 통한 프레임리스 창 이동 로직
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def wake_scrollbar(self):
        """스크롤 시 스크롤바 투명도 초기화 및 타이머 재시작"""
        self.fade_anim.stop()
        self.scrollbar_effect.setOpacity(1.0)
        self.fade_timer.start()

    def handle_range_changed(self, min_val, max_val):
        """새 메시지 추가 시 스크롤 최하단 이동"""
        self.scroll.verticalScrollBar().setValue(max_val)
        self.wake_scrollbar()

    def fade_out_scrollbar(self):
        """유휴 시간 경과 시 스크롤바 서서히 사라짐"""
        if self.scrollbar_effect.opacity() > 0:
            self.fade_anim.setStartValue(self.scrollbar_effect.opacity())
            self.fade_anim.setEndValue(0.0)
            self.fade_anim.start()

    def send_message(self):
        text = self.input_field.text().strip()
        if not text: return
        self.add_chat_bubble(text, is_me=True)
        self.input_field.clear()        
        QTimer.singleShot(500, lambda: self.add_chat_bubble(f"에코: {text}", is_me=False))
        
    def add_chat_bubble(self, text, is_me):
        """메시지 아이템을 레이아웃에 추가하고 스크롤 갱신 예약"""
        bubble = ChatItem(text, is_me)
        self.chat_layout.addWidget(bubble)
        QTimer.singleShot(0, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        """렌더링 후 스크롤을 끝으로 밀어넣음"""
        scrollbar = self.scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("BlahBlah")
    window = ChatInterface()
    window.show()
    sys.exit(app.exec())