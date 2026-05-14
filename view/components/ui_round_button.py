#============================================================
# - subject: ui_round_button.py
# - created: 2026-05-12
# - updated: 2026-05-14
# - summary: Smooth circular push button with hover states.
# - caution: Custom painting requires antialiasing enabled.
#============================================================
from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen

# 다이내믹 아일랜드 등에서 사용되는 정원(원형) 테두리의 플랫 버튼
class SmoothRoundButton(QPushButton):
    # 버튼 사이즈 및 커서 포인터 설정
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(26, 26)
        self.setCursor(Qt.PointingHandCursor)

    # 안티앨리어싱을 통해 클릭 상태(isDown)에 따라 매끄러운 둥근 배경 그리기
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(51, 51, 51) if self.isDown() else QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255, 25), 1.0))
        painter.drawEllipse(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1))
        super().paintEvent(event)