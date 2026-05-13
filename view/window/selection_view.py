from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QGraphicsOpacityEffect, QLabel
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Signal
from view.components.ui_scroll_area import SmoothScrollArea
from view.components.ui_round_button import SmoothRoundButton
from view.components.ui_menu_item import MenuListItem
from view.components.ui_dynamic_island import DynamicIsland
from view.configuration.app_texts import NO_MODELS_MSG, UNKNOWN_MODEL_NAME, UNKNOWN_MODEL_SIZE

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

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(16, 24, 8, 30)
        self.scroll_layout.setSpacing(12) 
        self.scroll_layout.setAlignment(Qt.AlignTop)
        

        self.scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll, 1)

        self.dynamic_island = DynamicIsland(self.container)
        self.dynamic_island.left_btn.clicked.connect(lambda: self.back_requested.emit())
        self.dynamic_island.right_btn.clicked.connect(lambda: self.window().close())

    def update_model_list(self, models, active_model=None):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not models:
            info_label = QLabel(NO_MODELS_MSG)
            info_label.setStyleSheet("color: #8E8E93; font-size: 12px; background: transparent; border: none; padding: 20px;")
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setWordWrap(True)
            self.scroll_layout.addWidget(info_label)
            return

        for model in sorted(models, key=lambda x: x.get('name', '')):
            model_name = model.get('name', UNKNOWN_MODEL_NAME)
            model_size = model.get('size', 0)

            if model_size > 0:
                size_gb = round(model_size / (1024**3), 2)
                subtitle = f"Size: {size_gb} GB"
            else:
                subtitle = UNKNOWN_MODEL_SIZE

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
        if hasattr(self, 'dynamic_island'):
            self.dynamic_island.update_position(self.width())