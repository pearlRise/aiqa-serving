import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QFrame
from PySide6.QtCore import Qt
from chat_view import ChatView

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(305, 655)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 메인 컨테이너 (둥근 모서리 등 스타일 유지)
        self.container = QWidget()
        self.container.setObjectName("MainBody")
        self.container.setStyleSheet("#MainBody { background-color: #ABC1D1; border: 1px solid #222; border-radius: 48px; }")
        self.setCentralWidget(self.container)

        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 화면 전환을 위한 스택 위젯
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)

        # 화면 등록
        self.chat_view = ChatView()
        # self.home_view = HomeView() # 나중에 추가할 곳
        
        self.stack.addWidget(self.chat_view) 
        # 우선 채팅창을 먼저 보여주도록 설정
        self.stack.setCurrentWidget(self.chat_view)

        # 다이내믹 아일랜드 (상단 고정 요소)
        self.island = QFrame(self.container)
        self.island.setFixedSize(120, 26)
        self.island.setStyleSheet("background-color: black; border-radius: 13px;")
        self.island.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.island.move(int((self.width() - self.island.width()) / 2), 8)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())