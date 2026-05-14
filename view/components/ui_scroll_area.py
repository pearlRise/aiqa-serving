#============================================================
# - subject: ui_scroll_area.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Smooth scrolling area with custom scrollbars.
# - caution: QPropertyAnimation may cause scroll conflicts.
#============================================================
from PySide6.QtWidgets import QScrollArea, QGraphicsOpacityEffect
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer

# 휠스크롤 애니메이션과 투명해지는 스크롤바를 지원하는 커스텀 스크롤 영역
class SmoothScrollArea(QScrollArea):
    # 스크롤바 CSS 및 페이드/이동 애니메이션 객체 초기화
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

    # 마우스/스크롤 발생 시 스크롤바를 나타내고 숨김 대기 타이머 재시작
    def show_scrollbar(self, *args):
        if self.scrollbar_anim.state() == QPropertyAnimation.Running: self.scrollbar_anim.stop()
        self.scroll_effect.setOpacity(1.0)
        self.scroll_timer.start(1500)

    # 타이머 만료 시 스크롤바를 서서히 투명하게 페이드아웃
    def hide_scrollbar(self):
        self.scrollbar_anim.start()

    # 마우스 휠 이벤트를 가로채어 스크롤 수치를 애니메이션으로 보간
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