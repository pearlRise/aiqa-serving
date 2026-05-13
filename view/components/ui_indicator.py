from PySide6.QtWidgets import QFrame

class IndicatorInfoCell(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("IndicatorInfoCell { background: transparent; border: none; border-radius: 0px; }")