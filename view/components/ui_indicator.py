#============================================================
# - subject: ui_indicator.py
# - created: 2026-05-12
# - updated: 2026-05-14
# - summary: Clickable indicator cell for system statuses.
# - caution: None.
#============================================================
from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Qt, Signal

# 홈 뷰 등의 상태 요약(예: Memory, Engine 등) 영역 클릭을 위한 투명 프레임
class IndicatorInfoCell(QFrame):
    clicked = Signal()
    # 커서 포인터 스타일 적용
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("IndicatorInfoCell { background: transparent; border: none; border-radius: 0px; }")
        self.setCursor(Qt.PointingHandCursor)
        
    # 프레임 좌클릭 발생 시 clicked 커스텀 시그널 방출
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)