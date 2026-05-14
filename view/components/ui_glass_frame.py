#============================================================
# - subject: ui_glass_frame.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Semi-transparent glassy frame base component.
# - caution: None.
#============================================================
from PySide6.QtWidgets import QFrame

# 둥근 테두리와 반투명 배경의 모피즘 효과를 적용할 수 있는 공통 프레임 상속체
class GlassFrame(QFrame):
    # 입력받은 radius 인자 기반으로 글래스 느낌의 QSS 템플릿 적용
    def __init__(self, radius=16, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            GlassFrame {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: {radius}px;
            }}
        """)