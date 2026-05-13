from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QFrame, QGraphicsOpacityEffect, QLabel
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation
from view.components.ui_scroll_area import SmoothScrollArea
from view.components.ui_round_button import SmoothRoundButton
from view.components.ui_chat_bubble import ChatItem
from view.components.ui_chat_input import CustomInput
from view.components.ui_dynamicIsland import DynamicIsland
from view.components.ui_internal_menu import InternalMenu

class ChatView(QWidget):
    def __init__(self):
        super().__init__()
        
        self.container = QWidget()
        self.container.setObjectName("MainBody")

        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)
        base_layout.addWidget(self.container)
        
        self.container.setStyleSheet("#MainBody { background-color: #000000; border: 1px solid #222; border-radius: 48px; }")        
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 10)
        self.main_layout.setSpacing(0) 

        self.top_bar = QFrame(self.container)
        self.top_bar.setFixedHeight(48)
        self.top_bar.setStyleSheet("QFrame { background-color: #212121; border: none; border-top-left-radius: 47px; border-top-right-radius: 47px; }")
        self.main_layout.addWidget(self.top_bar)

        self.dynamic_island = DynamicIsland(self.container)
        self.dynamic_island.right_btn.clicked.connect(lambda: self.window().close())
        self.back_btn = self.dynamic_island.left_btn # AppController 와의 호환성 유지

        self.scroll = SmoothScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none; background: transparent; width: 8px; margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.25); border-radius: 4px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: rgba(255, 255, 255, 0.4); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                height: 0px; background: none;
            }
        """)

        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(16, 30, 8, 16)
        self.chat_layout.setSpacing(0) 
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.chat_content)
        self.main_layout.addWidget(self.scroll, 1)

        self.internal_menu = InternalMenu(self.container)
        self.dynamic_island.mid_btn.clicked.connect(lambda: self.internal_menu.toggle(self.width()))

        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.update_visible_bubbles)
        self.last_width = self.width()

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
            current_text = self.last_chat_item.bubble.toPlainText()
            if current_text == "{...}":
                new_text = chunk
            else:
                new_text = current_text + chunk
            self.last_chat_item.update_text(new_text)
            self.last_chat_item.update_width(self.width())
            self.scroll_to_bottom()

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
        
        if hasattr(self, 'dynamic_island'):
            self.dynamic_island.update_position(self.width())
            
        if hasattr(self, 'internal_menu'):
            self.internal_menu.update_position(self.width())
            
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