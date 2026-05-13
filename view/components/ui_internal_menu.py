from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt
from view.components.ui_scroll_area import SmoothScrollArea

class InternalMenu(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 200)
        self.setStyleSheet("""
            QFrame { background-color: #FFFFFF; border: 1px solid #B0C4DE; border-radius: 12px; }
        """)
        self.hide()

        self.scroll = SmoothScrollArea(scrollbar_width=6, scrollbar_margin="4px 0px 4px 0px")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.layout = QVBoxLayout(self.content)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)
        
        for i in range(1, 16):
            lbl = QLabel(f"Dummy Item {i}")
            lbl.setStyleSheet("padding: 8px; font-size: 13px; color: #333333; background: #F5F7F9; border-radius: 6px; border: none;")
            self.layout.addWidget(lbl)
            
        self.scroll.setWidget(self.content)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.scroll)

    def toggle(self, parent_width):
        if self.isHidden():
            self.move(parent_width - 196, 50)
            self.show()
            self.raise_()
        else:
            self.hide()

    def update_position(self, parent_width):
        if not self.isHidden():
            self.move(parent_width - 196, 50)