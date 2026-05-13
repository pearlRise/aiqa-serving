from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Signal
from view.components.common_ui import SmoothScrollArea, SmoothRoundButton
from view.components.menu_ui import MenuListItem

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
        
        for i in range(1, 11):
            item = MenuListItem("📝", f"Template Menu {i}", "This is a dummy description.")
            self.scroll_layout.addWidget(item)

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        island_x = (self.width() - 120) // 2
        if hasattr(self, 'island'): self.island.move(island_x, 11)
        if hasattr(self, 'back_btn'): self.back_btn.move(island_x - 31, 11)
        if hasattr(self, 'menu_btn'): self.menu_btn.move(island_x + 125, 11)
        if hasattr(self, 'close_btn'): self.close_btn.move(island_x + 156, 11)

    def show_scrollbar(self, *args):
        if self.scrollbar_anim.state() == QPropertyAnimation.Running: self.scrollbar_anim.stop()
        self.scroll_effect.setOpacity(1.0)
        self.scroll_timer.start(1500)

    def hide_scrollbar(self):
        self.scrollbar_anim.start()
