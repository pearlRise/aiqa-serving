from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPainter

class MarqueeLabel(QLabel):
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

    def setText(self, text):
        self._text = text
        super().setText(text)
        self.check_scroll()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.check_scroll()

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

    def update_offset(self):
        self.offset -= 1
        fm = self.fontMetrics()
        text_width = fm.horizontalAdvance(self._text)
        if self.offset < -(text_width + self.gap):
            self.offset = 0
        self.update()

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