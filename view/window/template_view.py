#============================================================
# - subject: template_view.py
# - created: 2026-05-11
# - updated: 2026-05-14
# - summary: Dummy view for prompt templates navigation.
# - caution: None.
#============================================================
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Signal
from view.components.ui_scroll_area import SmoothScrollArea
from view.components.ui_round_button import SmoothRoundButton
from view.components.ui_menu_button import MenuButton

class TemplateView(QWidget):

    def __init__(self):
        super().__init__()
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 48, 0, 21) 
        self.main_layout.setSpacing(0)

        self.scroll = SmoothScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(16, 24, 8, 30)
        self.scroll_layout.setSpacing(12) 
        self.scroll_layout.setAlignment(Qt.AlignTop)
        
        for i in range(1, 11):
            item = MenuButton("📝", f"Template Menu {i}", "This is a dummy description.")
            self.scroll_layout.addWidget(item)

        self.scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll, 1)
