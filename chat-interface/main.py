import sys
import os
from datetime import datetime

# [최적화] macOS 및 Qt 내부의 불필요한 경고/디버그 로그 출력 억제
os.environ["QT_LOGGING_RULES"] = "qt.*=false"

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QScrollArea, QLabel, QFrame, 
    QGraphicsOpacityEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation

class ChatItem(QWidget):
    """개별 말풍선 위젯 (크기 자동 조절 및 텍스트 복사 지원)"""
    def __init__(self, text, is_me=False):
        super().__init__()
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 5, 0, 5)
        self.main_layout.setSpacing(5)

        # 1. 말풍선 텍스트 설정 (글자 단위 줄바꿈 꼼수 및 PlainText 강제)
        formatted_text = "\u200B".join(list(text))
        self.bubble = QLabel(formatted_text)
        self.bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.bubble.setCursor(Qt.IBeamCursor)
        self.bubble.setWordWrap(True)
        self.bubble.setTextFormat(Qt.PlainText) 
        
        # 2. 정밀한 너비 계산 (단문 잘림 방지 및 장문 자동 줄바꿈)
        fm = self.bubble.fontMetrics()
        real_text_width = fm.horizontalAdvance(text) + 34 # 텍스트폭 + 패딩(24) + 마진(10)
        max_bubble_width = 210
        
        if real_text_width < max_bubble_width:
            self.bubble.setFixedWidth(real_text_width)
        else:
            self.bubble.setFixedWidth(max_bubble_width)

        self.bubble.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        
        # 3. 말풍선 스타일 지정
        bg_color = "#FEE500" if is_me else "#FFFFFF"
        self.bubble.setStyleSheet(f"""
            color: #000000; 
            border-radius: 12px; 
            padding: 7px 12px; 
            font-size: 13px; 
            background-color: {bg_color};
            border: none;
        """)

        # 4. 시간 라벨 생성
        curr_time = datetime.now().strftime("%H:%M")
        self.time_label = QLabel(curr_time)
        self.time_label.setStyleSheet("color: #556677; font-size: 10px;")
        self.time_label.setAlignment(Qt.AlignBottom)

        # 5. 발신자에 따른 좌우 배치
        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(5)

        if is_me:
            self.main_layout.addStretch()
            self.content_layout.addWidget(self.time_label, alignment=Qt.AlignBottom)
            self.content_layout.addWidget(self.bubble)
            self.main_layout.addLayout(self.content_layout)
        else:
            self.content_layout.addWidget(self.bubble)
            self.content_layout.addWidget(self.time_label, alignment=Qt.AlignBottom)
            self.main_layout.addLayout(self.content_layout)
            self.main_layout.addStretch()


class ChatInterface(QMainWindow):
    """메인 채팅 인터페이스 (아이폰 미러링 스타일)"""
    def __init__(self):
        super().__init__()
        
        # 1. 윈도우 기본 설정
        self.setFixedSize(305, 655) 
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.container = QWidget()
        self.setCentralWidget(self.container)
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

        # 2. 다이내믹 아일랜드 
        self.main_layout.addSpacing(15) 
        self.island = QFrame()
        self.island.setFixedSize(120, 26) 
        self.island.setStyleSheet("background-color: black; border-radius: 13px;")
        self.main_layout.addWidget(self.island, alignment=Qt.AlignHCenter)
        
        # 3. 채팅 내역 스크롤 영역
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn) 
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollArea > QWidget > QWidget { border: none; background: transparent; }
            QScrollArea::viewport { border: none; background: transparent; }
            QScrollBar:vertical { border: none; background: transparent; width: 8px; margin: 0px; }                      
            QScrollBar::handle:vertical { background: rgba(0, 0, 0, 0.2); min-height: 30px; border-radius: 4px; }
            QScrollBar::handle:vertical:hover { background: rgba(0, 0, 0, 0.4); }
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical { height: 0px; width: 0px; border: none; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; border: none; }
        """)
        # 스크롤바 페이드아웃 효과 설정
        self.scrollbar_effect = QGraphicsOpacityEffect()
        self.scroll.verticalScrollBar().setGraphicsEffect(self.scrollbar_effect)
        
        self.fade_anim = QPropertyAnimation(self.scrollbar_effect, b"opacity")
        self.fade_anim.setDuration(300) 
        
        self.fade_timer = QTimer()
        self.fade_timer.setInterval(1500) # 1.5초 유휴 상태 대기
        self.fade_timer.setSingleShot(True)
        self.fade_timer.timeout.connect(self.fade_out_scrollbar)

        # 스크롤 이벤트 연결
        self.scroll.verticalScrollBar().valueChanged.connect(self.wake_scrollbar)
        self.scroll.verticalScrollBar().rangeChanged.connect(self.handle_range_changed)
        self.fade_timer.start()
        
        # 채팅 내용 컨테이너
        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent; border: none;")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(15, 10, 7, 10) 
        self.chat_layout.addStretch()
        
        self.scroll.setWidget(self.chat_content)
        self.main_layout.addWidget(self.scroll)
        
        # 4. 하단 입력 바
        self.input_container = QWidget()
        self.input_container.setFixedHeight(50) 
        self.input_container.setStyleSheet("background-color: transparent; border: none;")

        input_layout = QHBoxLayout(self.input_container)
        input_layout.setContentsMargins(15, 0, 15, 10) # 바닥 마진을 줘서 둥근 모서리에 안 닿게 조절
        input_layout.setSpacing(8)

        # 텍스트 입력창 (복사/붙여넣기 메뉴 및 포커스 강화)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Let's have a conversation!")
        self.input_field.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.input_field.setFocusPolicy(Qt.StrongFocus)
        self.input_field.setFixedHeight(32)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #BDC3C7; /* 아주 연한 테두리만 허용 */
                border-radius: 16px;
                padding: 0 12px;
                color: #000000;
                font-size: 14px;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)

        # 전송 버튼
        self.send_btn = QPushButton("↑")
        self.send_btn.setFixedSize(32, 32)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF; 
                color: white; 
                border-radius: 16px; 
                font-weight: bold; 
                font-size: 16px;
                border: none;
            }
            QPushButton:pressed { background-color: #0051A8; }
        """)
        self.send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        self.main_layout.addWidget(self.input_container)

        self.old_pos = None

    # --- 마우스 이벤트 (창 이동) ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = current_pos

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    # --- 스크롤바 제어 로직 ---
    def wake_scrollbar(self):
        """스크롤바를 즉시 표시하고 타이머 재시작"""
        if self.fade_anim.state() == QPropertyAnimation.Running:
            self.fade_anim.stop()
        self.scrollbar_effect.setOpacity(1.0)
        self.fade_timer.start()

    def handle_range_changed(self, min_val, max_val):
        """메시지 추가 등으로 스크롤 범위가 변할 때의 처리"""
        self.scroll.verticalScrollBar().setValue(max_val)
        self.wake_scrollbar()

    def fade_out_scrollbar(self):
        """1.5초 유휴 후 부드럽게 사라짐"""
        current_opacity = self.scrollbar_effect.opacity()
        if current_opacity > 0:
            self.fade_anim.setStartValue(current_opacity)
            self.fade_anim.setEndValue(0.0)
            self.fade_anim.start()

    def update_scroll(self, min_val, max_val):
        """내용 변경 시 스크롤바 최하단 고정"""
        self.scroll.verticalScrollBar().setValue(max_val)

    # --- 대화 처리 로직 ---
    def send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return
            
        self.add_chat_bubble(text, is_me=True)
        QTimer.singleShot(10, self.input_field.clear)        
        QTimer.singleShot(500, lambda: self.add_chat_bubble(f"에코: {text}", is_me=False))
        
    def add_chat_bubble(self, text, is_me):
        bubble = ChatItem(text, is_me)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        
        self.chat_content.adjustSize()
        QApplication.processEvents()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Ollama Talk")
    window = ChatInterface()
    window.show()
    sys.exit(app.exec())