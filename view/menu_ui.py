from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QFont
from view.common_ui import GlassFrame

class IndicatorInfoCell(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("IndicatorInfoCell { background: transparent; border: none; border-radius: 0px; }")

class MenuListItem(GlassFrame):
    clicked = Signal(str)
    def __init__(self, icon, title, subtitle):
        super().__init__(radius=16)
        self.setFixedHeight(72)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.is_active = False
        self.setObjectName("MenuItem")
        
        self.default_bg = "rgba(255, 255, 255, 0.05)"
        self.hover_bg = "rgba(255, 255, 255, 0.12)"
        self.pressed_bg = "rgba(255, 255, 255, 0.2)"
        self._apply_bg(self.default_bg)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        self.icon_label = QLabel(icon)
        self.icon_label.setFont(QFont("Apple Color Emoji", 24))
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent; border: none;")
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignVCenter)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: bold; background: transparent; border: none;")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet("color: #8E8E93; font-size: 12px; background: transparent; border: none;")
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.subtitle_label)
        
        layout.addWidget(self.icon_label)
        layout.addLayout(text_layout)
        layout.addStretch()
        
    def _apply_bg(self, bg_color):
        self.setStyleSheet(f"#MenuItem {{ background-color: {bg_color}; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; }}")

    def set_active(self, is_active):
        self.is_active = is_active
        color, bg = ("#E6A23C", "rgba(230, 162, 60,") if is_active else ("#FFFFFF", "rgba(255, 255, 255,")
        self.default_bg, self.hover_bg, self.pressed_bg = f"{bg} 0.15)", f"{bg} 0.25)", f"{bg} 0.35)" if is_active else (f"{bg} 0.05)", f"{bg} 0.12)", f"{bg} 0.2)")
        self.title_label.setStyleSheet(f"color: {color}; font-size: 15px; font-weight: bold; background: transparent; border: none;")
        self._apply_bg(self.default_bg)

    def enterEvent(self, event): self._apply_bg(self.hover_bg); super().enterEvent(event)
    def leaveEvent(self, event): self._apply_bg(self.default_bg); super().leaveEvent(event)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self._apply_bg(self.pressed_bg)
        super().mousePressEvent(event)
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.underMouse(): self._apply_bg(self.hover_bg); self.clicked.emit(self.title_label.text())
            else: self._apply_bg(self.default_bg)
        super().mouseReleaseEvent(event)