from PySide6.QtWidgets import QFrame

class GlassFrame(QFrame):
    def __init__(self, radius=16, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            GlassFrame {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: {radius}px;
            }}
        """)