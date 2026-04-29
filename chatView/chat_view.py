from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QTextBrowser
from PySide6.QtCore import Qt
from components import BubbleFrame

class ChatItem(QWidget):
    def __init__(self, text, is_me=False, sender_name="", is_consecutive=False):
        super().__init__()
        self.is_me, self.is_consecutive = is_me, is_consecutive
        self.has_tail, self.last_window_width = True, 305
        
        self.main_layout = QVBoxLayout(self)
        self.top_margin = 4 if is_consecutive else 12
        self.main_layout.setContentsMargins(0, self.top_margin, 0, 0)
        self.main_layout.setSpacing(2)

        self.has_name_label = not is_me and not is_consecutive and sender_name
        if self.has_name_label:
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
        
        self.doc = self.bubble.document()
        self.bubble.setFont(self.doc.defaultFont())
        self.update_width(305)

        if is_me:
            self.bubble_hlayout.addStretch()
            self.bubble_hlayout.addWidget(self.bg_frame)
        else:
            self.bubble_hlayout.addWidget(self.bg_frame)
            self.bubble_hlayout.addStretch()

    def update_width(self, window_width=None):
        # (기존 update_width 로직과 동일)
        pass

class ChatView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # 스크롤 영역 및 입력창 설정 (기존 ChatInterface의 UI 부분)
        self.scroll = QScrollArea()
        self.chat_content = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_content)
        # ... (이전 코드의 UI 구성 로직) ...
        self.layout.addWidget(self.scroll)