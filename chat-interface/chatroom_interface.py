import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QScrollArea, 
                             QLabel, QFrame, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt

class ChatItem(QWidget):
    """말풍선 하나를 담당하는 위젯"""
    def __init__(self, text, is_me=False):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # 실제 텍스트가 들어갈 라벨
        self.bubble = QLabel(text)
        self.bubble.setWordWrap(True)
        self.bubble.setMaximumWidth(280) # 말풍선 최대 너비 제한
        
        # 메신저 스타일 스타일시트 (나: 노란색, 상대: 흰색)
        if is_me:
            self.bubble.setStyleSheet("""
                background-color: #FEE500; 
                color: #000000;
                border-radius: 10px;
                padding: 8px 12px;
            """)
            layout.addStretch() # 왼쪽에 빈 공간을 넣어 오른쪽 정렬
            layout.addWidget(self.bubble)
        else:
            self.bubble.setStyleSheet("""
                background-color: #FFFFFF; 
                color: #000000;
                border-radius: 10px;
                padding: 8px 12px;
            """)
            layout.addWidget(self.bubble)
            layout.addStretch() # 오른쪽에 빈 공간을 넣어 왼쪽 정렬

class ChatInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("aiqa-serving chat")
        self.resize(400, 600)
        self.setStyleSheet("background-color: #ABC1D1;") # 카톡 배경색 느낌

        # 메인 레이아웃 구성
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        self.layout.setContentsMargins(0, 0, 0, 10)

        # 1. 채팅창 영역 (스크롤 가능)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        
        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.addStretch() # 메시지가 위에서부터 차곡차곡 쌓이게
        
        self.scroll.setWidget(self.chat_content)
        self.layout.addWidget(self.scroll)

        # 2. 하단 입력 영역
        input_container = QWidget()
        input_container.setStyleSheet("background-color: #FFFFFF;")
        input_layout = QHBoxLayout(input_container)