#============================================================
# - subject: ui_marquee_label.py
# - created: 2026-05-12
# - updated: 2026-05-14
# - summary: Scrolling text label for overflowing content.
# - caution: Continuous QTimer usage may affect performance.
#============================================================
from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPainter

# 컴포넌트 너비를 벗어나는 긴 텍스트를 좌측으로 자동 스크롤 시키는 라벨
class MarqueeLabel(QLabel):
    # 초기화 및 텍스트 렌더링에 필요한 오프셋 타이머 설정
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._text = text
        self.offset = 0
        self.gap = 40
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_offset)
        self.is_scrolling = False
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

    def minimumSizeHint(self):
        return QSize(10, super().minimumSizeHint().height())

    # 텍스트가 변경될 때 스크롤 애니메이션 필요 여부 다시 확인
    def setText(self, text):
        self._text = text
        super().setText(text)
        self.check_scroll()

    # 라벨 크기 변경 시 스크롤 애니메이션 필요 여부 다시 확인
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.check_scroll()

    # 텍스트 폭과 위젯 너비를 비교하여 스크롤 타이머 시작 또는 중지
    def check_scroll(self):
        fm = self.fontMetrics()
        if fm.horizontalAdvance(self._text) > self.width() and self.width() > 0:
            if not self.is_scrolling:
                self.is_scrolling = True
                self.offset = 0
                self.timer.start(30)
        else:
            self.is_scrolling = False
            self.timer.stop()
            self.offset = 0
        self.update()

    # 타이머 틱마다 텍스트의 오프셋을 줄여 좌측 이동 연출 (끝에 도달 시 루프)
    def update_offset(self):
        self.offset -= 1
        fm = self.fontMetrics()
        text_width = fm.horizontalAdvance(self._text)
        if self.offset < -(text_width + self.gap):
            self.offset = 0
        self.update()

    # QPainter로 흐르는 텍스트 원본 및 복사본(이어지는 글자) 수동 렌더링
    def paintEvent(self, event):
        if not self.is_scrolling:
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setPen(self.palette().windowText().color())
        painter.setFont(self.font())
        fm = self.fontMetrics()
        text_width = fm.horizontalAdvance(self._text)
        painter.drawText(self.offset, 0, text_width, self.height(), Qt.AlignVCenter | Qt.AlignLeft, self._text)
        painter.drawText(self.offset + text_width + self.gap, 0, text_width, self.height(), Qt.AlignVCenter | Qt.AlignLeft, self._text)