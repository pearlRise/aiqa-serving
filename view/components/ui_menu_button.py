#============================================================
# - subject: ui_menu_button.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Reusable glassy menu button with visual states.
# - caution: Emits custom signals upon mouse release events.
#============================================================
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QFont
from view.components.ui_glass_frame import GlassFrame
from view.components.ui_marquee_label import MarqueeLabel

# 리스트 뷰 및 설정 메뉴에서 널리 쓰이는 투명한 라운드 버튼 클래스
class MenuButton(GlassFrame):
    clicked = Signal(str)
    # 레이아웃 구성, 아이콘 및 MarqueeLabel 초기화
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
        
    # 버튼 상태에 따른 동적 배경 및 테두리 색상 QSS 적용
    def _apply_bg(self, bg_color, border_color="rgba(255, 255, 255, 0.1)"):
        self.setStyleSheet(f"#MenuButton {{ background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 16px; }}")

    # 선택 활성화 상태 및 로딩 여부에 맞춰 텍스트 컬러와 배경 변경
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

    # 마우스 호버 진입 시 밝기 강조 효과
    def enterEvent(self, event):
        if self.isEnabled(): self._apply_bg(self.hover_bg, self.border_color); super().enterEvent(event)
    # 마우스 호버 이탈 시 복구
    def leaveEvent(self, event):
        if self.isEnabled(): self._apply_bg(self.default_bg, self.border_color); super().leaveEvent(event)
    # 마우스 클릭(Pressed) 시 더 밝아지는 효과
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled(): self._apply_bg(self.pressed_bg, self.border_color); super().mousePressEvent(event)
    # 마우스 놓음(Release) 시 클릭 시그널 전달
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled():
            if self.underMouse(): self._apply_bg(self.hover_bg, self.border_color); self.clicked.emit(self.title_label.text())
            else: self._apply_bg(self.default_bg, self.border_color)
        super().mouseReleaseEvent(event)

    # 비활성화 시 컴포넌트 전체에 투명도 40% 효과 부여
    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        if not enabled:
            eff = QGraphicsOpacityEffect(self)
            eff.setOpacity(0.4)
            self.setGraphicsEffect(eff)
        else:
            self.setGraphicsEffect(None)