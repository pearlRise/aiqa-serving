from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QGraphicsOpacityEffect, QLabel
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Signal
from view.view_components import SmoothScrollArea, MenuListItem, SmoothRoundButton

class SelectionView(QWidget):
    back_requested = Signal()
    model_selected = Signal(str)

    def __init__(self):
        super().__init__()
        
        self.container = QWidget()
        self.container.setObjectName("MainBody")

        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)
        base_layout.addWidget(self.container)
        
        self.container.setStyleSheet("""
            #MainBody { 
                background-color: #000000; 
                border: 1px solid #222; 
                border-radius: 48px; 
            }
        """)        
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 21) 
        self.main_layout.setSpacing(0)

        self.top_bar = QFrame(self.container)
        self.top_bar.setFixedHeight(48)
        self.top_bar.setStyleSheet("QFrame { background-color: #212121; border: none; border-top-left-radius: 47px; border-top-right-radius: 47px; }")
        self.main_layout.addWidget(self.top_bar)

        self.scroll = SmoothScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none; background: transparent; width: 8px; margin: 24px 0px 24px 0px;
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
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(16, 24, 8, 30)
        self.scroll_layout.setSpacing(12) 
        self.scroll_layout.setAlignment(Qt.AlignTop)
        
        # 모델 리스트는 MainController에서 `update_model_list`를 통해 동적으로 채워집니다.

        self.scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll, 1)

        self.island = QFrame(self.container)
        self.island.setFixedSize(120, 26)
        self.island.setStyleSheet("background-color: black; border-radius: 13px;")
        self.island.raise_()

        self.back_btn = SmoothRoundButton("←", self.container)
        self.back_btn.setStyleSheet("QPushButton { background: transparent; font-size: 15px; color: white; border: none; padding: 0px; }")
        self.back_btn.clicked.connect(lambda: self.back_requested.emit())
        
        self.menu_btn = SmoothRoundButton("≡", self.container)
        self.menu_btn.setStyleSheet("QPushButton { background: transparent; font-size: 17px; color: white; border: none; padding-bottom: 3px; }")

        self.close_btn = SmoothRoundButton("✕", self.container)
        self.close_btn.setStyleSheet("QPushButton { background: transparent; font-size: 14px; font-weight: bold; color: white; border: none; padding-bottom: 2px; }")
        self.close_btn.clicked.connect(lambda: self.window().close())

        self.back_btn.raise_()
        self.menu_btn.raise_()
        self.close_btn.raise_()

    def update_model_list(self, models, active_model=None):
        # 기존 위젯 모두 삭제
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not models:
            info_label = QLabel("No models found on the Ollama server.\nYou can pull a model using 'ollama pull <model_name>'.")
            info_label.setStyleSheet("color: #8E8E93; font-size: 12px; background: transparent; border: none; padding: 20px;")
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setWordWrap(True)
            self.scroll_layout.addWidget(info_label)
            return

        # 모델 이름순으로 정렬하여 추가
        for model in sorted(models, key=lambda x: x.get('name', '')):
            model_name = model.get('name', 'Unknown Model')
            model_size = model.get('size', 0)

            if model_size > 0:
                size_gb = round(model_size / (1024**3), 2)
                subtitle = f"Size: {size_gb} GB"
            else:
                subtitle = "Size: Unknown"

            item = MenuListItem("🤖", model_name, subtitle)
            if active_model == model_name:
                item.set_active(True)
            item.clicked.connect(self.model_selected.emit)
            self.scroll_layout.addWidget(item)

    def set_active_model(self, active_model_name):
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if isinstance(widget, MenuListItem):
                is_active = (widget.title_label.text() == active_model_name)
                widget.set_active(is_active)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        island_x = (self.width() - 120) // 2
        if hasattr(self, 'island'):
            self.island.move(island_x, 11)
        if hasattr(self, 'back_btn'):
            self.back_btn.move(island_x - 31, 11)
        if hasattr(self, 'menu_btn'):
            self.menu_btn.move(island_x + 125, 11)
        if hasattr(self, 'close_btn'):
            self.close_btn.move(island_x + 156, 11)

    def show_scrollbar(self, *args):
        if self.scrollbar_anim.state() == QPropertyAnimation.Running:
            self.scrollbar_anim.stop()
        self.scroll_effect.setOpacity(1.0)
        self.scroll_timer.start(1500)

    def hide_scrollbar(self):
        self.scrollbar_anim.start()