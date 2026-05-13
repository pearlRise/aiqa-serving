from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QCursor, QFont, QPainter
from view.components.ui_glass_frame import GlassFrame

class MarqueeLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._text = text
        self.offset = 0
        self.gap = 40
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_offset)
        self.is_scrolling = False
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

    def minimumSizeHint(self):
        return QSize(10, super().minimumSizeHint().height())

    def setText(self, text):
        self._text = text
        super().setText(text)
        self.check_scroll()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.check_scroll()

    def check_scroll(self):
        fm = self.fontMetrics()
        if fm.horizontalAdvance(self._text) > self.width() and self.width() > 0:
            if not self.is_scrolling:
                self.is_scrolling = True
                self.offset = 0
                self.timer.start(30)
        else:
            self.is_scrolling = False
            self.timer.stop()
            self.offset = 0
        self.update()

    def update_offset(self):
        self.offset -= 1
        fm = self.fontMetrics()
        text_width = fm.horizontalAdvance(self._text)
        if self.offset < -(text_width + self.gap):
            self.offset = 0
        self.update()

    def paintEvent(self, event):
        if not self.is_scrolling:
            super().paintEvent(event)
            return
        
        painter = QPainter(self)
        painter.setPen(self.palette().windowText().color())
        painter.setFont(self.font())
        
        fm = self.fontMetrics()
        text_width = fm.horizontalAdvance(self._text)
        
        painter.drawText(self.offset, 0, text_width, self.height(), Qt.AlignVCenter | Qt.AlignLeft, self._text)
        painter.drawText(self.offset + text_width + self.gap, 0, text_width, self.height(), Qt.AlignVCenter | Qt.AlignLeft, self._text)

class MenuButton(GlassFrame):
    clicked = Signal(str)
    def __init__(self, icon, title, subtitle):
        super().__init__(radius=16)
        self.setFixedHeight(64)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.is_active = False
        self.setObjectName("MenuButton")
        
        self.default_bg = "rgba(255, 255, 255, 0.05)"
        self.hover_bg = "rgba(255, 255, 255, 0.12)"
        self.pressed_bg = "rgba(255, 255, 255, 0.2)"
        self._apply_bg(self.default_bg)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)
        self.icon_label = QLabel(icon)
        self.icon_label.setFont(QFont("Apple Color Emoji", 24))
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent; border: none;")
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignVCenter)
        self.title_label = MarqueeLabel(title)
        self.title_label.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: bold; background: transparent; border: none;")
        self.subtitle_label = MarqueeLabel(subtitle)
        self.subtitle_label.setStyleSheet("color: #8E8E93; font-size: 12px; background: transparent; border: none;")
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.subtitle_label)
        
        layout.addWidget(self.icon_label)
        layout.addLayout(text_layout)
        
    def _apply_bg(self, bg_color):
        self.setStyleSheet(f"#MenuButton {{ background-color: {bg_color}; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; }}")

    def set_active(self, is_active):
        self.is_active = is_active
        color, bg = ("#E6A23C", "rgba(230, 162, 60,") if is_active else ("#FFFFFF", "rgba(255, 255, 255,")
        self.default_bg, self.hover_bg, self.pressed_bg = f"{bg} 0.15)", f"{bg} 0.25)", f"{bg} 0.35)" if is_active else (f"{bg} 0.05)", f"{bg} 0.12)", f"{bg} 0.2)")
        self.title_label.setStyleSheet(f"color: {color}; font-size: 15px; font-weight: bold; background: transparent; border: none;")
        self._apply_bg(self.default_bg)

    def enterEvent(self, event):
        if self.isEnabled(): self._apply_bg(self.hover_bg); super().enterEvent(event)
    def leaveEvent(self, event):
        if self.isEnabled(): self._apply_bg(self.default_bg); super().leaveEvent(event)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled(): self._apply_bg(self.pressed_bg); super().mousePressEvent(event)
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled():
            if self.underMouse(): self._apply_bg(self.hover_bg); self.clicked.emit(self.title_label.text())
            else: self._apply_bg(self.default_bg)
        super().mouseReleaseEvent(event)

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        if not enabled:
            eff = QGraphicsOpacityEffect(self)
            eff.setOpacity(0.4)
            self.setGraphicsEffect(eff)
        else:
            self.setGraphicsEffect(None)