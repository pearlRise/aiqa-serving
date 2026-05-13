from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from view.components.ui_round_button import SmoothRoundButton

class DynamicIsland(QWidget):
    def __init__(self, parent=None, left_text="i", mid_text="≡", right_text="✕"):
        super().__init__(parent)
        
        self.island = QFrame(self)
        self.island.setFixedSize(120, 26)
        self.island.setStyleSheet("background-color: black; border-radius: 13px;")
        
        self.island_layout = QVBoxLayout(self.island)
        self.island_layout.setContentsMargins(12, 4, 12, 4)
        self.island_layout.setSpacing(2)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: white; font-size: 10px; font-weight: bold; background: transparent;")
        self.progress_label.setAlignment(Qt.AlignCenter)
        
        self.progress_track = QFrame()
        self.progress_track.setFixedHeight(4)
        self.progress_track.setStyleSheet("background-color: #333333; border-radius: 2px;")
        
        self.progress_chunk = QFrame(self.progress_track)
        self.progress_chunk.setFixedSize(60, 4)
        self.progress_chunk.setStyleSheet("background-color: #E6A23C; border-radius: 2px;")
        
        self.island_layout.addWidget(self.progress_label)
        self.island_layout.addWidget(self.progress_track)
        self.progress_label.hide()
        self.progress_track.hide()
        
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self._update_progress)
        self.progress_val = 0

        self.left_btn = SmoothRoundButton(left_text, self)
        self.left_btn.setStyleSheet("QPushButton { background: transparent; font-size: 15px; color: white; border: none; padding: 0px; }")
        
        mid_font_size = "15px" if mid_text == "?" else "17px"
        self.mid_btn = SmoothRoundButton(mid_text, self)
        self.mid_btn.setStyleSheet(f"QPushButton {{ background: transparent; font-size: {mid_font_size}; color: white; border: none; padding-bottom: 3px; }}")

        self.right_btn = SmoothRoundButton(right_text, self)
        self.right_btn.setStyleSheet("QPushButton { background: transparent; font-size: 14px; font-weight: bold; color: white; border: none; padding-bottom: 2px; }")
        
        self.island.move(31, 0)
        self.left_btn.move(0, 0)
        self.mid_btn.move(156, 0)
        self.right_btn.move(187, 0)
        
        self.setFixedSize(213, 26)

    def _update_progress(self):
        max_x = self.progress_track.width()
        
        self.progress_val += 3
        if self.progress_val > max_x:
            self.progress_val = -self.progress_chunk.width()
            
        self.progress_chunk.move(self.progress_val, 0)

    def show_progress(self, text):
        self.progress_label.setText(text)
        self.progress_label.show()
        self.progress_track.show()
        self.progress_val = -self.progress_chunk.width()
        self.progress_chunk.move(self.progress_val, 0)
        self.progress_timer.start(20)

    def hide_progress(self):
        self.progress_label.hide()
        self.progress_track.hide()
        self.progress_timer.stop()

    def update_position(self, parent_width):
        island_x = (parent_width - 120) // 2
        self.move(island_x - 31, 11)
        self.raise_()