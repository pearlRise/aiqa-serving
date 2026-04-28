import sys
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QScrollArea, QLabel, QFrame, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation
from PySide6.QtGui import QTextOption

class ChatItem(QWidget):
    """개별 말풍선 위젯"""
    def __init__(self, text, is_me=False):
        super().__init__()
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 5, 0, 5)
        self.main_layout.setSpacing(5)

        # [수정] 텍스트의 모든 글자 사이에 '폭이 없는 공백(\u200B)'을 끼워 넣음.
        # 이렇게 하면 시각적으로는 전혀 티가 안 나지만, QLabel은 "아! 글자마다 띄어쓰기가 있네?" 
        # 하고 착각해서 영역 끝에 닿으면 즉시 글자 단위로 줄바꿈을 해버림.
        formatted_text = "\u200B".join(list(text))
        
        # 1. 말풍선 생성 및 줄바꿈 설정
        self.bubble = QLabel(formatted_text)
        self.bubble.setWordWrap(True) 
        
        self.bubble.setMaximumWidth(200)
        from PySide6.QtWidgets import QSizePolicy
        self.bubble.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        bg_color = "#FEE500" if is_me else "#FFFFFF"
        
        # [추가 팁] line-height와 padding을 살짝 넉넉히 주면 한글 받침이 잘리는 것도 방지돼
        common_style = f"""
            color: #000000; 
            border-radius: 12px; 
            padding: 10px 12px; 
            font-size: 13px; 
            line-height: 1.3;
            background-color: {bg_color};
        """
        self.bubble.setStyleSheet(common_style)
        # 2. 시간 라벨 (이전과 동일)
        curr_time = datetime.now().strftime("%H:%M")
        self.time_label = QLabel(curr_time)
        self.time_label.setStyleSheet("color: #556677; font-size: 10px;")
        self.time_label.setAlignment(Qt.AlignBottom)

        # 3. 레이아웃 배치
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

        # 2. 메인 바디 컨테이너
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

        # 3. 다이내믹 아일랜드 
        self.main_layout.addSpacing(15) 
        
        self.island = QFrame()
        self.island.setFixedSize(120, 26) 
        self.island.setStyleSheet("background-color: black; border-radius: 13px;")
        self.main_layout.addWidget(self.island, alignment=Qt.AlignHCenter)
        
        # 4. 채팅 내역 영역 (스크롤)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn) 
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 스크롤바 8px 및 투명화 QSS 설정
        self.scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;           
                margin: 0px; 
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.2); 
                min-height: 30px;
                border-radius: 4px;   
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 0, 0, 0.4);
            }
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
                border: none; background: none; height: 0px; width: 0px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # [신규] 스크롤바 페이드아웃 효과 로직
        self.scrollbar_effect = QGraphicsOpacityEffect()
        self.scroll.verticalScrollBar().setGraphicsEffect(self.scrollbar_effect)
        
        self.fade_anim = QPropertyAnimation(self.scrollbar_effect, b"opacity")
        self.fade_anim.setDuration(300) # 0.3초 동안 부드럽게 사라짐
        
        self.fade_timer = QTimer()
        self.fade_timer.setInterval(2000) # 2초 유휴 상태 대기
        self.fade_timer.setSingleShot(True)
        self.fade_timer.timeout.connect(self.fade_out_scrollbar)

        # 스크롤 이벤트 연결
        self.scroll.verticalScrollBar().valueChanged.connect(self.wake_scrollbar)
        self.scroll.verticalScrollBar().rangeChanged.connect(self.update_scroll)
        
        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent;")
        
        self.chat_layout = QVBoxLayout(self.chat_content)
        # 좌측 15px / 우측 7px + 스크롤바 8px = 양쪽 정확히 15px 유지
        self.chat_layout.setContentsMargins(15, 10, 7, 10) 
        self.chat_layout.addStretch()
        
        self.scroll.setWidget(self.chat_content)
        self.main_layout.addWidget(self.scroll)
        
        # 5. 하단 입력 바
        self.input_container = QWidget()
        self.input_container.setFixedHeight(50) 
        
        input_layout = QHBoxLayout(self.input_container)
        input_layout.setContentsMargins(15, 0, 15, 0) 
        input_layout.setSpacing(8)

        input_height = 32
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("iMessage")
        self.input_field.setFixedHeight(input_height)
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid #CCC;
                border-radius: {input_height // 2}px;
                padding: 0 12px;
                color: #000000;
                font-size: 14px;
            }}
        """)
        self.input_field.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton("↑")
        self.send_btn.setFixedSize(input_height, input_height)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #007AFF; 
                color: white; 
                border-radius: {input_height // 2}px; 
                font-weight: bold; 
                font-size: 16px;
                border: none;
            }}
            QPushButton:pressed {{ background-color: #0051A8; }}
        """)
        self.send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        self.main_layout.addWidget(self.input_container)

        self.old_pos = None

    # --- 마우스 이벤트를 이용한 창 이동 로직 (최신 API 적용) ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # globalPos() 대신 globalPosition().toPoint() 사용
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = current_pos

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    # --- 스크롤바 페이드아웃 및 위치 고정 제어 ---
    def wake_scrollbar(self):
        """스크롤이 움직이면 투명도를 1.0으로 복구하고 타이머 재시작"""
        if self.fade_anim.state() == QPropertyAnimation.Running:
            self.fade_anim.stop()
        self.scrollbar_effect.setOpacity(1.0)
        self.fade_timer.start()

    def fade_out_scrollbar(self):
        """2초 유휴 후 스크롤바 투명하게 숨김"""
        current_opacity = self.scrollbar_effect.opacity()
        self.fade_anim.setStartValue(current_opacity)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.start()

    def update_scroll(self, min_val, max_val):
        """범위 변경 시 바닥으로 위치 고정 (핸들 크기만 비례해서 줄어듦)"""
        self.scroll.verticalScrollBar().setValue(max_val)

    # --- 채팅 처리 로직 ---
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
        
        # 레이아웃 강제 갱신 -> rangeChanged 시그널 즉시 발생 -> update_scroll 실행됨
        self.chat_content.adjustSize()
        QApplication.processEvents() 

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Ollama Talk")
    window = ChatInterface()
    window.show()
    sys.exit(app.exec())