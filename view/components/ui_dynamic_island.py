import time
from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from view.components.ui_round_button import SmoothRoundButton
from view.components.ui_marquee_label import MarqueeLabel

class DynamicIsland(QWidget):
    def __init__(self, parent=None, left_text="i", mid_text="≡", right_text="✕"):
        super().__init__(parent)
        
        self.island = QFrame(self)
        self.island.setFixedSize(120, 26)
        self.island.setStyleSheet("background-color: black; border-radius: 13px;")
        
        self.island_layout = QVBoxLayout(self.island)
        self.island_layout.setContentsMargins(12, 4, 12, 4)
        self.island_layout.setSpacing(2)
        
        self.progress_label = MarqueeLabel("")
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

        self.active_tasks = []
        self.task_info = {}

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

    def show_progress(self, task_id, text):
        if task_id in self.task_info and 'timer' in self.task_info[task_id]:
            self.task_info[task_id]['timer'].stop()
            self.task_info[task_id]['timer'].deleteLater()

        if task_id in self.active_tasks:
            self.active_tasks.remove(task_id)
        self.active_tasks.append(task_id)

        self.task_info[task_id] = {
            'text': text,
            'start_time': time.time(),
            'fill_bar': False
        }
        self._update_display()

    def hide_progress(self, task_id, end_text=None, fill_bar=False):
        if task_id not in self.task_info: return
        
        if end_text:
            self.task_info[task_id]['text'] = end_text
            self.task_info[task_id]['fill_bar'] = fill_bar
            self.task_info[task_id]['start_time'] = time.time()
            self._update_display()

        elapsed = time.time() - self.task_info[task_id]['start_time']
        is_top = (self.active_tasks and self.active_tasks[-1] == task_id)
        
        if elapsed < 1.0 and is_top:
            delay_ms = int((1.0 - elapsed) * 1000)
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda t=task_id: self._remove_task(t))
            self.task_info[task_id]['timer'] = timer
            timer.start(delay_ms)
        else:
            self._remove_task(task_id)

    def _remove_task(self, task_id):
        if task_id in self.active_tasks:
            self.active_tasks.remove(task_id)
        if task_id in self.task_info:
            if 'timer' in self.task_info[task_id]:
                self.task_info[task_id]['timer'].stop()
                self.task_info[task_id]['timer'].deleteLater()
            del self.task_info[task_id]
        self._update_display()
        
    def _update_display(self):
        if self.active_tasks:
            top_task = self.active_tasks[-1]
            text = self.task_info[top_task]['text']
            self.progress_label.setText(text)
            self.progress_label.show()
            self.progress_track.show()
            
            if self.task_info[top_task].get('fill_bar', False):
                self.progress_timer.stop()
                self.progress_chunk.setFixedSize(self.progress_track.width(), 4)
                self.progress_chunk.move(0, 0)
            else:
                if not self.progress_timer.isActive():
                    self.progress_chunk.setFixedSize(60, 4)
                    self.progress_val = -self.progress_chunk.width()
                    self.progress_chunk.move(self.progress_val, 0)
                    self.progress_timer.start(20)
        else:
            self.progress_label.hide()
            self.progress_track.hide()
            self.progress_timer.stop()

    def update_position(self, parent_width):
        island_x = (parent_width - 120) // 2
        self.move(island_x - 31, 11)
        self.raise_()