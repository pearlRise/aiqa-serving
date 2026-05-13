from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QFont
from view.components.ui_glass_frame import GlassFrame
from view.components.ui_marquee_label import MarqueeLabel

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
        self.border_color = "rgba(255, 255, 255, 0.1)"
        self._apply_bg(self.default_bg, self.border_color)

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
        
    def _apply_bg(self, bg_color, border_color="rgba(255, 255, 255, 0.1)"):
        self.setStyleSheet(f"#MenuButton {{ background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 16px; }}")

    def set_active(self, is_active, is_loading=False):
        self.is_active = is_active
        if is_active:
            if is_loading:
                color, bg = "#E6A23C", "rgba(230, 162, 60,"  # Orange
                self.border_color = "rgba(230, 162, 60, 0.4)"
            else:
                color, bg = "#67C23A", "rgba(103, 194, 58,"  # Green
                self.border_color = "rgba(103, 194, 58, 0.4)"
            self.default_bg, self.hover_bg, self.pressed_bg = (f"{bg} 0.15)", f"{bg} 0.25)", f"{bg} 0.35)")
        else:
            color, bg = "#FFFFFF", "rgba(255, 255, 255,"
            self.border_color = "rgba(255, 255, 255, 0.1)"
            self.default_bg, self.hover_bg, self.pressed_bg = (f"{bg} 0.05)", f"{bg} 0.12)", f"{bg} 0.2)")
            
        self.title_label.setStyleSheet(f"color: {color}; font-size: 15px; font-weight: bold; background: transparent; border: none;")
        self._apply_bg(self.default_bg, self.border_color)

    def enterEvent(self, event):
        if self.isEnabled(): self._apply_bg(self.hover_bg, self.border_color); super().enterEvent(event)
    def leaveEvent(self, event):
        if self.isEnabled(): self._apply_bg(self.default_bg, self.border_color); super().leaveEvent(event)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled(): self._apply_bg(self.pressed_bg, self.border_color); super().mousePressEvent(event)
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled():
            if self.underMouse(): self._apply_bg(self.hover_bg, self.border_color); self.clicked.emit(self.title_label.text())
            else: self._apply_bg(self.default_bg, self.border_color)
        super().mouseReleaseEvent(event)

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        if not enabled:
            eff = QGraphicsOpacityEffect(self)
            eff.setOpacity(0.4)
            self.setGraphicsEffect(eff)
        else:
            self.setGraphicsEffect(None)