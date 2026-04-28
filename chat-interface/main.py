import sys
import math
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QScrollArea, QLabel, QFrame, 
    QGraphicsOpacityEffect, QTextBrowser, QTextEdit, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Signal
from PySide6.QtGui import QTextOption, QPainter, QPainterPath, QColor

class BubbleFrame(QFrame):
    """iMessage 스타일의 꼬리가 달린 커스텀 프레임"""
    def __init__(self, is_me):
        super().__init__()
        self.is_me = is_me
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        w, h = self.width(), self.height()
        r, t = 15, 8 

        if self.is_me:
            path.moveTo(r, 0); path.lineTo(w - r - t, 0); path.quadTo(w - t, 0, w - t, r)
            path.lineTo(w - t, h - r - 5); path.quadTo(w - t, h - 5, w, h)
            path.quadTo(w - t - 2, h - 2, w - t - 8, h - 8); path.lineTo(r, h - 8)
            path.quadTo(0, h - 8, 0, h - 8 - r); path.lineTo(0, r); path.quadTo(0, 0, r, 0)
        else:
            path.moveTo(r + t, 0); path.lineTo(w - r, 0); path.quadTo(w, 0, w, r)
            path.lineTo(w, h - r - 8); path.quadTo(w, h - 8, w - r, h - 8)
            path.lineTo(r + t + 8, h - 8); path.quadTo(t + 2, h - 2, 0, h)
            path.quadTo(t, h - 5, t, h - r - 5); path.lineTo(t, r); path.quadTo(t, 0, r + t, 0)
        painter.fillPath(path, QColor("#FEE500") if self.is_me else QColor("#FFFFFF"))

class ChatItem(QWidget):
    def __init__(self, text, is_me=False):
        super().__init__()
        self.is_me, self.layout = is_me, QHBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)
        self.bg_frame = BubbleFrame(is_me)
        self.bg_layout = QVBoxLayout(self.bg_frame)
        self.tail_width, self.padding_x, self.padding_y = 8, 12, 7
        
        margin = (self.padding_x, self.padding_y, self.padding_x + self.tail_width, self.padding_y + 8) if is_me else \
                 (self.padding_x + self.tail_width, self.padding_y, self.padding_x, self.padding_y + 8)
        self.bg_layout.setContentsMargins(*margin)
        
        self.bubble = QTextBrowser()
        self.bubble.setFrameShape(QFrame.NoFrame)
        self.bubble.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bubble.setStyleSheet("background: transparent; color: #000000;")
        font = self.bubble.font(); font.setPixelSize(13); self.bubble.setFont(font)
        self.doc = self.bubble.document(); self.doc.setDefaultFont(font); self.doc.setDocumentMargin(0)
        option = QTextOption(); option.setWrapMode(QTextOption.WrapAnywhere); self.doc.setDefaultTextOption(option)
        self.bubble.setPlainText(text); self.doc.setTextWidth(10000)
        self.pure_ideal_width = math.ceil(self.doc.idealWidth())
        self.bg_layout.addWidget(self.bubble)
        self.time_label = QLabel(datetime.now().strftime("%H:%M"))
        self.time_label.setStyleSheet("color: #556677; font-size: 10px;")
        
        if is_me:
            self.layout.addStretch(); self.layout.addWidget(self.time_label, alignment=Qt.AlignBottom); self.layout.addWidget(self.bg_frame)
        else:
            self.layout.addWidget(self.bg_frame); self.layout.addWidget(self.time_label, alignment=Qt.AlignBottom); self.layout.addStretch()
        self.update_width(305)

    def update_width(self, window_width):
        max_text_width = int(window_width * 0.688) - (self.padding_x * 2) - self.tail_width
        actual_text_width = min(self.pure_ideal_width, max_text_width) + 2
        self.doc.setTextWidth(actual_text_width if self.pure_ideal_width > max_text_width else -1)
        text_height = math.ceil(self.doc.size().height()) + 2
        self.bubble.setFixedSize(actual_text_width, text_height)
        self.bg_frame.setFixedSize(actual_text_width + (self.padding_x * 2) + self.tail_width, text_height + (self.padding_y * 2) + 8)
        self.setFixedHeight(self.bg_frame.height() + 10)

class CustomInput(QTextEdit):
    """iMessage 스타일: 내용에 따라 높이가 변하며 엔터로 전송"""
    returnPressed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setPlaceholderText("Message...")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.NoFrame)
        font = self.font(); font.setPixelSize(14); self.setFont(font)
        # 입력창 내부 스크롤바 스타일
        self.setStyleSheet("""
            QTextEdit { 
                background-color: #FFFFFF; color: #000000;
                border-radius: 16px; padding: 5px 12px; 
                border: 1px solid #BDC3C7;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 4px; /* 입력창은 더 얇게 */
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.1);
                border-radius: 2px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                height: 0px;
                background: none;
            }
        """)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            self.returnPressed.emit()
        else:
            super().keyPressEvent(event)

class ChatInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(305, 655); self.resize(305, 655)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint); self.setAttribute(Qt.WA_TranslucentBackground)
        self.container = QWidget(); self.setCentralWidget(self.container)
        self.container.setStyleSheet("#MainBody { background-color: #ABC1D1; border: 1px solid #222; border-radius: 48px; }")
        self.container.setObjectName("MainBody")
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 15); self.main_layout.setSpacing(10)
        
        # 아일랜드
        self.main_layout.addSpacing(15)
        self.island = QFrame(); self.island.setFixedSize(120, 26); 
        self.island.setStyleSheet("background-color: black; border-radius: 13px;")
        self.main_layout.addWidget(self.island, alignment=Qt.AlignHCenter)
        
        # 채팅 영역 (Stretch 1)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none; background: transparent;
                width: 8px; margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.15); border-radius: 4px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 0, 0, 0.3);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                height: 0px; background: none;
            }
        """)

        self.scroll.verticalScrollBar().rangeChanged.connect(self.scroll_to_bottom)
        self.chat_content = QWidget(); self.chat_content.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_content); self.chat_layout.setContentsMargins(15, 10, 7, 10); self.chat_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.chat_content)
        self.main_layout.addWidget(self.scroll, 1)

        # 입력 영역 (Stretch 0)
        self.input_container = QWidget()
        self.input_layout = QHBoxLayout(self.input_container)
        self.input_layout.setContentsMargins(15, 0, 15, 10); self.input_layout.setSpacing(8); self.input_layout.setAlignment(Qt.AlignBottom)
        
        self.input_field = CustomInput()
        self.input_field.textChanged.connect(self.adjust_input_height)
        self.input_field.returnPressed.connect(self.send_message)
        
        self.send_btn = QPushButton("↑"); self.send_btn.setFixedSize(32, 32)
        self.send_btn.setStyleSheet("QPushButton { background-color: #007AFF; color: white; border-radius: 16px; font-weight: bold; font-size: 16px; border: none; }")
        self.send_btn.clicked.connect(self.send_message)
        
        self.input_layout.addWidget(self.input_field); self.input_layout.addWidget(self.send_btn)
        self.main_layout.addWidget(self.input_container, 0)
        
        self.resizing, self.resize_margin, self.old_pos = False, 10, None

    def adjust_input_height(self):
        """내용이 한 줄일 때는 32px로 고정, 두 줄부터 유동적으로 확장 (중복 제거본)"""
        doc = self.input_field.document()
        doc_height = doc.size().height()
        
        # 14px 폰트 기준, 문서 높이가 22px 이하면 확실히 '한 줄'이야.
        # 이때는 계산하지 말고 그냥 32px로 딱 고정해버리는 게 가장 깔끔해.
        if doc_height <= 22:
            new_height = 32
        else:
            # 두 줄부터는 실제 높이에 여백(+11)을 줘서 자연스럽게 늘어나게 해.
            new_height = max(32, min(120, int(doc_height) + 11))
        
        if self.input_field.height() != new_height:
            self.input_field.setFixedHeight(new_height)
            # 입력창 높이가 변할 때 말풍선을 밀어올리는 '푸시' 효과
            QTimer.singleShot(0, self.scroll_to_bottom)

    def send_message(self):
        """메시지 전송 시 높이를 즉시 32px로 복구"""
        text = self.input_field.toPlainText().strip()
        if not text:
            return
        
        self.add_chat_bubble(text, is_me=True)
        self.input_field.clear()
        
        # 전송 버튼 누르자마자 높이를 32px로 초기화해서 딜레이를 없앰
        self.input_field.setFixedHeight(32)
        
        # 테스트용 에코 봇 응답
        QTimer.singleShot(500, lambda: self.add_chat_bubble(f"에코: {text}", is_me=False))

    def add_chat_bubble(self, text, is_me):
        """메시지 추가 시에도 스크롤 하단 이동 보장"""
        bubble = ChatItem(text, is_me)
        bubble.update_width(self.width())
        self.chat_layout.addWidget(bubble)
        # rangeChanged 시그널이 처리되지만, 명시적으로 한 번 더 호출 (안전장치)
        QTimer.singleShot(10, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        """스크롤바를 항상 최하단으로 유지"""
        scrollbar = self.scroll.verticalScrollBar()
        # 새 메시지가 추가되어 maximum() 값이 갱신되었을 때 해당 위치로 이동
        scrollbar.setValue(scrollbar.maximum())

    def adjust_input_height(self):
        """내용이 한 줄일 때는 32px로 고정하고, 그 이상일 때만 동적으로 확장"""
        doc = self.input_field.document()
        doc_height = doc.size().height()
        
        # 14px 폰트 기준, 문서 높이가 약 22px 이하이면 한 줄로 간주
        if doc_height <= 22:
            new_height = 32
        else:
            # 두 줄부터는 실제 높이에 패딩(약 10~12px)을 더해 유동적으로 조절
            new_height = max(32, min(120, int(doc_height) + 11))
        
        if self.input_field.height() != new_height:
            # 높이 변화가 확실할 때만 업데이트하여 레이아웃 흔들림 방지
            self.input_field.setFixedHeight(new_height)
            # 입력창이 커질 때 말풍선을 밀어올리는 효과 유지
            QTimer.singleShot(0, self.scroll_to_bottom)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        for i in range(self.chat_layout.count()):
            widget = self.chat_layout.itemAt(i).widget()
            if isinstance(widget, ChatItem): widget.update_width(self.width())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            if pos.x() > self.width() - self.resize_margin or pos.y() > self.height() - self.resize_margin: self.resizing = True
            else: self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        if pos.x() > self.width() - self.resize_margin and pos.y() > self.height() - self.resize_margin: self.setCursor(Qt.SizeFDiagCursor)
        elif pos.x() > self.width() - self.resize_margin: self.setCursor(Qt.SizeHorCursor)
        elif pos.y() > self.height() - self.resize_margin: self.setCursor(Qt.SizeVerCursor)
        else: self.setCursor(Qt.ArrowCursor)
        if self.resizing: self.resize(max(self.minimumWidth(), pos.x()), max(self.minimumHeight(), pos.y()))
        elif self.old_pos:
            curr = event.globalPosition().toPoint(); self.move(self.pos() + curr - self.old_pos); self.old_pos = curr

    def mouseReleaseEvent(self, event): self.resizing = False; self.old_pos = None

if __name__ == "__main__":
    app = QApplication(sys.argv); 
    window = ChatInterface(); 
    window.show(); 
    sys.exit(app.exec())