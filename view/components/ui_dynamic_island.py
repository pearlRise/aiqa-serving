#============================================================
# - subject: ui_dynamic_island.py
# - created: 2026-05-12
# - updated: 2026-05-14
# - summary: Custom dynamic island UI for progress tracking.
# - caution: Manage task timers to prevent memory leaks.
#============================================================
import time
from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from view.components.ui_round_button import SmoothRoundButton
from view.components.ui_marquee_label import MarqueeLabel

# 화면 상단에서 작업 상태, 뒤로 가기, 메뉴 진입을 담당하는 오버레이 컴포넌트
class DynamicIsland(QWidget):
    # 아일랜드 컨테이너 및 프로그레스 애니메이션 요소, 버튼 초기화
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

        # 다수의 백그라운드 작업 상태를 저장하여 우선순위 관리
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

    # 무한히 우측으로 흐르는 프로그레스 바 애니메이션 틱 계산
    def _update_progress(self):
        max_x = self.progress_track.width()
        
        self.progress_val += 3
        if self.progress_val > max_x:
            self.progress_val = -self.progress_chunk.width()
            
        self.progress_chunk.move(self.progress_val, 0)

    # 특정 ID의 작업을 등록하고 상태 표시(텍스트/로딩바) 시작
    def show_progress(self, task_id, text):
        """
        POLICY - Background Task Priority (LIFO)
        1. Policy Description
            - Manages the display queue of multiple concurrent background tasks.
        2. Policy Constraints
            - New incoming tasks must suspend the existing task's UI updates and be shown at the top.
            - To prevent timer conflicts and memory leaks, existing timers for the task must be stopped and deleted (`deleteLater`) immediately.
        """
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

    # 특정 ID 작업 종료 시 텍스트를 업데이트하고 즉시 또는 지연 숨김
    def hide_progress(self, task_id, end_text=None, fill_bar=False):
        """
        POLICY - UI Anti-Flicker Prevention
        1. Policy Description
            - Ensures smooth visual transitions for the dynamic island when tasks end.
        2. Policy Constraints
            - If a task completes in less than 1.0 second, it causes a visual flicker.
            - The top exposed task must be delayed using a `QTimer` for the remaining duration before hiding to prevent this abrupt UI change.
        """
        if task_id not in self.task_info: return
        
        if end_text:
            self.task_info[task_id]['text'] = end_text
            self.task_info[task_id]['fill_bar'] = fill_bar
            self.task_info[task_id]['start_time'] = time.time()
            self._update_display()

        elapsed = time.time() - self.task_info[task_id]['start_time']
        is_top = (self.active_tasks and self.active_tasks[-1] == task_id)
        
        # 작업이 너무 빨리 종료되어 깜빡임이 생기는 것을 방지하는 최소 노출 타이머
        if elapsed < 1.0 and is_top:
            delay_ms = int((1.0 - elapsed) * 1000)
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda t=task_id: self._remove_task(t))
            self.task_info[task_id]['timer'] = timer
            timer.start(delay_ms)
        else:
            self._remove_task(task_id)

    # 작업 큐 및 정보에서 완전히 제거하고 UI 상태 갱신
    def _remove_task(self, task_id):
        if task_id in self.active_tasks:
            self.active_tasks.remove(task_id)
        if task_id in self.task_info:
            if 'timer' in self.task_info[task_id]:
                self.task_info[task_id]['timer'].stop()
                self.task_info[task_id]['timer'].deleteLater()
            del self.task_info[task_id]
        self._update_display()
        
    # 큐에 남은 작업이 있다면 표시 갱신, 없다면 완전히 숨김 처리
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

    # 메인 윈도우 리사이즈 시 중앙 상단에 아일랜드 정렬 유지
    def update_position(self, parent_width):
        island_x = (parent_width - 120) // 2
        self.move(island_x - 31, 11)
        self.raise_()