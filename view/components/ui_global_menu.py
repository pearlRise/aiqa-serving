from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt
from view.components.ui_scroll_area import SmoothScrollArea

class GlobalMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hide()
        self.setStyleSheet("background: transparent;")
        
        self.menu_frame = QFrame(self)
        self.menu_frame.setFixedSize(198, 230)
        self.menu_frame.setStyleSheet("""
            QFrame { background-color: #1C1C1E; border: 1px solid #333333; border-radius: 8px; }
        """)

        self.scroll = SmoothScrollArea(scrollbar_width=6, scrollbar_margin="4px 0px 4px 0px")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.layout = QVBoxLayout(self.content)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        for i in range(1, 16):
            btn = QPushButton(f"Dummy Item {i}")
            btn.setFixedHeight(36)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    color: #E0E0E0; background-color: transparent; text-align: left;
                    padding-left: 16px; font-size: 13px; border: none; border-radius: 0px;
                }
                QPushButton:hover { background-color: #2C2C2E; }
                QPushButton:pressed { background-color: #3A3A3C; }
            """)
            self.layout.addWidget(btn)
            
            if i < 15:
                line = QFrame()
                line.setFixedHeight(1)
                line.setStyleSheet("background-color: #333333; border: none;")
                self.layout.addWidget(line)
            
        self.scroll.setWidget(self.content)
        
        self.main_layout = QVBoxLayout(self.menu_frame)
        self.main_layout.setContentsMargins(1, 8, 1, 8)
        self.main_layout.addWidget(self.scroll)

    def toggle(self, parent_width, parent_height):
        if self.isHidden():
            self.setFixedSize(parent_width, parent_height)
            self.menu_frame.move(parent_width - 214, 50)
            self.show()
            self.raise_()
        else:
            self.hide()

    def update_position(self, parent_width, parent_height):
        if not self.isHidden():
            self.setFixedSize(parent_width, parent_height)
            self.menu_frame.move(parent_width - 214, 50)
            
    def mousePressEvent(self, event):
        if not self.menu_frame.geometry().contains(event.position().toPoint()):
            self.hide()
            event.accept()
        else:
            super().mousePressEvent(event)