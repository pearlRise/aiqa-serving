from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Qt, Signal

class IndicatorInfoCell(QFrame):
    clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("IndicatorInfoCell { background: transparent; border: none; border-radius: 0px; }")
        self.setCursor(Qt.PointingHandCursor)
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)