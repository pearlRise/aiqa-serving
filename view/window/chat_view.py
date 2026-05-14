#============================================================
# - subject: chat_view.py
# - created: 2026-05-11
# - updated: 2026-05-14
# - summary: Chat interface view with message bubbling and input.
# - caution: Ensure width updates on window resize for bubbles.
#============================================================
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation
from view.components.ui_scroll_area import SmoothScrollArea
from view.components.ui_round_button import SmoothRoundButton
from view.components.ui_chat_bubble import ChatItem
from view.components.ui_chat_input import CustomInput

class ChatView(QWidget):
    def __init__(self):
        super().__init__()
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 48, 0, 10)
        self.main_layout.setSpacing(0) 

        self.scroll = SmoothScrollArea(scrollbar_margin="0px")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(16, 30, 8, 16)
        self.chat_layout.setSpacing(0) 
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.chat_content)
        self.main_layout.addWidget(self.scroll, 1)

        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.update_visible_bubbles)
        self.last_width = self.width()

        # UI 렌더링 병목 해소를 위한 스트리밍 청크 버퍼 및 타이머
        self.stream_buffer = ""
        self.stream_timer = QTimer(self)
        self.stream_timer.timeout.connect(self.flush_stream_buffer)

        self.scroll.verticalScrollBar().valueChanged.connect(self.update_visible_bubbles)

        self.input_container = QWidget()
        self.input_layout = QHBoxLayout(self.input_container)
        self.input_layout.setContentsMargins(16, 8, 16, 16)
        self.input_layout.setSpacing(8)
        self.input_layout.setAlignment(Qt.AlignBottom)
        
        self.input_field = CustomInput()
        self.input_field.textChanged.connect(self.adjust_input_height)
        
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
        
        self.input_layout.addWidget(self.input_field)
        self.input_layout.addWidget(self.send_btn)
        self.main_layout.addWidget(self.input_container, 0)

        self.last_sender_id = None
        self.last_chat_item = None

        self.input_field.setFocus()
        
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

    def update_last_bubble_stream(self, chunk):
        if self.last_chat_item and not self.last_chat_item.is_me:
            # 매 토큰마다 무거운 UI 레이아웃 연산을 하지 않고 버퍼에 누적 후 타이머 시작
            self.stream_buffer += chunk
            if not self.stream_timer.isActive():
                self.stream_timer.start(50)  # 50ms (초당 20프레임) 간격으로 한 번에 갱신

    def flush_stream_buffer(self):
        if not self.stream_buffer or not self.last_chat_item:
            self.stream_timer.stop()
            return
            
        current_text = self.last_chat_item.bubble.toPlainText()
        new_text = self.stream_buffer if current_text == "Thinking..." else current_text + self.stream_buffer
        self.last_chat_item.update_text(new_text)
        self.last_chat_item.update_width(self.width())
        QTimer.singleShot(0, self.scroll_to_bottom)
        
        self.stream_buffer = ""
        self.stream_timer.stop()

    def adjust_input_height(self):
        doc = self.input_field.document()
        doc_height = doc.size().height()
        
        if doc_height <= 22:
            new_height = 44
        else:
            new_height = max(44, min(120, int(doc_height) + 26))
            
        self.input_field.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded if new_height >= 120 else Qt.ScrollBarAlwaysOff
        )
            
        if self.input_field.height() != new_height:
            self.input_field.setFixedHeight(new_height)
            QTimer.singleShot(0, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        scrollbar = self.scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        if self.width() != self.last_width:
            self.last_width = self.width()
            
            for i in range(self.chat_layout.count()):
                item = self.chat_layout.itemAt(i)
                widget = item.widget() if item else None
                if isinstance(widget, ChatItem):
                    widget.needs_width_update = True
            
            self.resize_timer.start(100)

    def update_visible_bubbles(self):
        scroll_y = self.scroll.verticalScrollBar().value()
        viewport_height = self.scroll.viewport().height()
        
        buffer = 150 
        visible_top = scroll_y - buffer
        visible_bottom = scroll_y + viewport_height + buffer

        for i in range(self.chat_layout.count()):
            item = self.chat_layout.itemAt(i)
            widget = item.widget() if item else None
            if isinstance(widget, ChatItem) and widget.needs_width_update:
                widget_y = widget.pos().y()
                if visible_top <= widget_y <= visible_bottom:
                    widget.update_width(self.width())
                    widget.needs_width_update = False

    def set_send_button_state(self, state):
        if state == "stop":
            self.send_btn.setText("■")
            self.send_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #FF3B30; color: white; 
                    border-radius: 20px;
                    font-weight: bold; font-size: 14px; border: none; 
                }
                QPushButton:pressed { background-color: #C02E24; }
            """)
        else:
            self.send_btn.setText("↑")
            self.send_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #007AFF; color: white; 
                    border-radius: 20px;
                    font-weight: bold; font-size: 16px; border: none; 
                }
                QPushButton:pressed { background-color: #0051A8; }
            """)