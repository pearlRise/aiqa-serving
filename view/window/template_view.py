from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Signal
from view.components.ui_scroll_area import SmoothScrollArea
from view.components.ui_round_button import SmoothRoundButton
from view.components.ui_menu_item import MenuListItem
from view.components.ui_dynamic_island import DynamicIsland

class TemplateView(QWidget):
    back_requested = Signal()

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
        
        for i in range(1, 11):
            item = MenuListItem("📝", f"Template Menu {i}", "This is a dummy description.")
            self.scroll_layout.addWidget(item)

        self.scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll, 1)

        self.dynamic_island = DynamicIsland(self.container)
        self.dynamic_island.left_btn.clicked.connect(lambda: self.back_requested.emit())
        self.dynamic_island.right_btn.clicked.connect(lambda: self.window().close())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'dynamic_island'): 
            self.dynamic_island.update_position(self.width())
