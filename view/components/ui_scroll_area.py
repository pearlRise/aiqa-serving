from PySide6.QtWidgets import QScrollArea, QGraphicsOpacityEffect
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer

class SmoothScrollArea(QScrollArea):
    def __init__(self, parent=None, scrollbar_width=8, scrollbar_margin="24px 0px 24px 0px"):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                border: none; background: transparent; width: {scrollbar_width}px; margin: {scrollbar_margin};
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.25); border-radius: {scrollbar_width // 2}px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background: rgba(255, 255, 255, 0.4); }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                height: 0px; background: none;
            }}
        """)
        
        self.target_val = 0
        self.anim = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.setDuration(400)

        self.scroll_effect = QGraphicsOpacityEffect(self.verticalScrollBar())
        self.verticalScrollBar().setGraphicsEffect(self.scroll_effect)
        self.scroll_effect.setOpacity(0.0)
        
        self.scroll_timer = QTimer(self)
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self.hide_scrollbar)
        
        self.scrollbar_anim = QPropertyAnimation(self.scroll_effect, b"opacity")
        self.scrollbar_anim.setDuration(300)
        self.scrollbar_anim.setStartValue(1.0)
        self.scrollbar_anim.setEndValue(0.0)
        
        self.verticalScrollBar().valueChanged.connect(self.show_scrollbar)
        self.verticalScrollBar().rangeChanged.connect(self.show_scrollbar)

    def show_scrollbar(self, *args):
        if self.scrollbar_anim.state() == QPropertyAnimation.Running: self.scrollbar_anim.stop()
        self.scroll_effect.setOpacity(1.0)
        self.scroll_timer.start(1500)

    def hide_scrollbar(self):
        self.scrollbar_anim.start()

    def wheelEvent(self, event):
        delta_y = event.angleDelta().y()
        if not event.pixelDelta().isNull() or (delta_y != 0 and abs(delta_y) % 120 != 0):
            super().wheelEvent(event)
            self.target_val = self.verticalScrollBar().value()
            return
        bar = self.verticalScrollBar()
        if self.anim.state() != QPropertyAnimation.Running:
            self.target_val = bar.value()
        step = event.angleDelta().y()
        self.target_val = max(bar.minimum(), min(bar.maximum(), self.target_val - step))
        self.anim.setEndValue(self.target_val)
        self.anim.start()