from PySide6.QtWidgets import QWidget, QFrame
from view.components.ui_common import SmoothRoundButton

class DynamicIsland(QWidget):
    def __init__(self, parent=None, left_text="←", mid_text="≡", right_text="✕"):
        super().__init__(parent)
        
        self.island = QFrame(self)
        self.island.setFixedSize(120, 26)
        self.island.setStyleSheet("background-color: black; border-radius: 13px;")
        
        self.left_btn = SmoothRoundButton(left_text, self)
        self.left_btn.setStyleSheet("QPushButton { background: transparent; font-size: 15px; color: white; border: none; padding: 0px; }")
        
        mid_font_size = "15px" if mid_text == "?" else "17px"
        self.mid_btn = SmoothRoundButton(mid_text, self)
        self.mid_btn.setStyleSheet(f"QPushButton {{ background: transparent; font-size: {mid_font_size}; color: white; border: none; padding-bottom: 3px; }}")

        self.right_btn = SmoothRoundButton(right_text, self)
        self.right_btn.setStyleSheet("QPushButton { background: transparent; font-size: 14px; font-weight: bold; color: white; border: none; padding-bottom: 2px; }")
        
        # 부모 위젯 내부에서의 절대 좌표 고정
        self.island.move(31, 0)
        self.left_btn.move(0, 0)
        self.mid_btn.move(156, 0)
        self.right_btn.move(187, 0)
        
        self.setFixedSize(213, 26)

    def update_position(self, parent_width):
        island_x = (parent_width - 120) // 2
        # 화면 중앙을 기준으로 계산된 오프셋 적용
        self.move(island_x - 31, 11)
        self.raise_()