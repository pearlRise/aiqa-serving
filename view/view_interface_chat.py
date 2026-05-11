from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QFrame, QGraphicsOpacityEffect, QLabel
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation
from view.view_components import ChatItem, CustomInput

# 4.1 채팅 인터페이스 전체 레이아웃 및 스크롤 영역 관리
class ChatView(QWidget):
    def __init__(self):
        super().__init__()
        
        self.container = QWidget()
        self.container.setObjectName("MainBody")

        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)
        base_layout.addWidget(self.container)
        
        self.container.setStyleSheet("#MainBody { background-color: #ABC1D1; border: 1px solid #222; border-radius: 48px; }")        
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 10)
        self.main_layout.setSpacing(0) 
        self.main_layout.addSpacing(2)

        self.back_btn = QPushButton("‹", self.container)
        self.back_btn.setFixedSize(30, 30)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setStyleSheet("""
            QPushButton { background-color: #007AFF; font-size: 24px; font-weight: bold; border: none; border-radius: 15px; color: white; padding-bottom: 2px; }
            QPushButton:pressed { background-color: #0051A8; }
        """)
        
        self.menu_btn = QPushButton("≡", self.container)
        self.menu_btn.setFixedSize(30, 30)
        self.menu_btn.setCursor(Qt.PointingHandCursor)
        self.menu_btn.setStyleSheet("""
            QPushButton { background-color: #007AFF; font-size: 20px; font-weight: bold; border: none; border-radius: 15px; color: white; }
            QPushButton:pressed { background-color: #0051A8; }
        """)

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

        self.scroll_effect = QGraphicsOpacityEffect(self.scroll.verticalScrollBar())
        self.scroll.verticalScrollBar().setGraphicsEffect(self.scroll_effect)
        self.scroll_effect.setOpacity(0.0)
        
        self.scroll_timer = QTimer(self)
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self.hide_scrollbar)
        
        self.scrollbar_anim = QPropertyAnimation(self.scroll_effect, b"opacity")
        self.scrollbar_anim.setDuration(300)
        self.scrollbar_anim.setStartValue(1.0)
        self.scrollbar_anim.setEndValue(0.0)
        
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

        self.dropdown_menu = QFrame(self.container)
        self.dropdown_menu.setFixedSize(180, 200)
        self.dropdown_menu.setStyleSheet("""
            QFrame { background-color: #FFFFFF; border: 1px solid #B0C4DE; border-radius: 12px; }
        """)
        self.dropdown_menu.hide()

        self.dropdown_scroll = QScrollArea()
        self.dropdown_scroll.setWidgetResizable(True)
        self.dropdown_scroll.setFrameShape(QFrame.NoFrame)
        self.dropdown_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.dropdown_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none; background: transparent; width: 6px; margin: 4px 0px 4px 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.15); border-radius: 3px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: rgba(0, 0, 0, 0.3); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                height: 0px; background: none;
            }
        """)

        self.dropdown_scroll_effect = QGraphicsOpacityEffect(self.dropdown_scroll.verticalScrollBar())
        self.dropdown_scroll.verticalScrollBar().setGraphicsEffect(self.dropdown_scroll_effect)
        self.dropdown_scroll_effect.setOpacity(0.0)
        
        self.dropdown_scroll_timer = QTimer(self)
        self.dropdown_scroll_timer.setSingleShot(True)
        self.dropdown_scroll_timer.timeout.connect(self.hide_dropdown_scrollbar)
        
        self.dropdown_scrollbar_anim = QPropertyAnimation(self.dropdown_scroll_effect, b"opacity")
        self.dropdown_scrollbar_anim.setDuration(300)
        self.dropdown_scrollbar_anim.setStartValue(1.0)
        self.dropdown_scrollbar_anim.setEndValue(0.0)
        
        self.dropdown_scroll.verticalScrollBar().valueChanged.connect(self.show_dropdown_scrollbar)
        self.dropdown_scroll.verticalScrollBar().rangeChanged.connect(self.show_dropdown_scrollbar)
        
        self.dropdown_content = QWidget()
        self.dropdown_content.setStyleSheet("background: transparent;")
        self.dropdown_layout = QVBoxLayout(self.dropdown_content)
        self.dropdown_layout.setContentsMargins(8, 8, 8, 8)
        self.dropdown_layout.setSpacing(4)
        
        for i in range(1, 16):
            lbl = QLabel(f"Dummy Item {i}")
            lbl.setStyleSheet("padding: 8px; font-size: 13px; color: #333333; background: #F5F7F9; border-radius: 6px; border: none;")
            self.dropdown_layout.addWidget(lbl)
            
        self.dropdown_scroll.setWidget(self.dropdown_content)
        
        self.dropdown_main_layout = QVBoxLayout(self.dropdown_menu)
        self.dropdown_main_layout.setContentsMargins(0, 0, 0, 0)
        self.dropdown_main_layout.addWidget(self.dropdown_scroll)
        
        self.menu_btn.clicked.connect(self.toggle_dropdown)

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
        
        self.back_btn.raise_()
        self.menu_btn.raise_()

    # 4.2 스크롤바 페이드 인/아웃 제어 로직
    def show_scrollbar(self, *args):
        if self.scrollbar_anim.state() == QPropertyAnimation.Running:
            self.scrollbar_anim.stop()
        self.scroll_effect.setOpacity(1.0)
        self.scroll_timer.start(1500)

    def hide_scrollbar(self):
        self.scrollbar_anim.start()

    def show_dropdown_scrollbar(self, *args):
        if self.dropdown_scrollbar_anim.state() == QPropertyAnimation.Running:
            self.dropdown_scrollbar_anim.stop()
        self.dropdown_scroll_effect.setOpacity(1.0)
        self.dropdown_scroll_timer.start(1500)

    def hide_dropdown_scrollbar(self):
        self.dropdown_scrollbar_anim.start()

    def toggle_dropdown(self):
        if self.dropdown_menu.isHidden():
            self.dropdown_menu.move(self.width() - 196, 50)
            self.dropdown_menu.show()
            self.dropdown_menu.raise_()
        else:
            self.dropdown_menu.hide()

    # 4.3 새로운 채팅 말풍선 추가 및 연속 메시지 그룹화
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

    # 4.3.1 마지막 AI 말풍선의 내용을 실시간으로 갱신 (Streaming)
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

    # 4.4 입력 내용에 따른 입력창 높이 동적 조절
    def adjust_input_height(self):
        doc = self.input_field.document()
        doc_height = doc.size().height()
        
        if doc_height <= 22:
            new_height = 44
        else:
            new_height = max(44, min(120, int(doc_height) + 26))
            
        # 1.3 입력창이 최대 높이(120px)에 도달했을 때만 스크롤바 노출
        self.input_field.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded if new_height >= 120 else Qt.ScrollBarAlwaysOff
        )
            
        if self.input_field.height() != new_height:
            self.input_field.setFixedHeight(new_height)
            QTimer.singleShot(0, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        scrollbar = self.scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    # 4.5 창 크기 변경 시 성능 최적화를 위한 지연 처리(Debounce)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        if hasattr(self, 'back_btn'):
            island_x = (self.width() - 120) // 2
            self.back_btn.move(island_x - 35, 6)
        if hasattr(self, 'menu_btn'):
            island_x = (self.width() - 120) // 2
            self.menu_btn.move(island_x + 125, 6)
            
        if hasattr(self, 'dropdown_menu') and not self.dropdown_menu.isHidden():
            self.dropdown_menu.move(self.width() - 196, 50)
            
        if self.width() != self.last_width:
            self.last_width = self.width()
            
            for i in range(self.chat_layout.count()):
                item = self.chat_layout.itemAt(i)
                widget = item.widget() if item else None
                if isinstance(widget, ChatItem):
                    widget.needs_width_update = True
            
            # 디바운싱: 드래그가 멈추고 100ms 후에 한 번만 재계산
            self.resize_timer.start(100)

    # 4.6 현재 가시 영역에 있는 말풍선 위젯만 선택적 갱신
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