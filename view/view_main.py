import sys
import os
import atexit
import signal

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from ollama.server_manager import ServerManager
from ollama.chat_manager import ChatController

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QFrame, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QPoint, QEvent, QTimer

from view.view_interface_main import HomeView
from view.view_chat_interface import ChatView

# 1.1 메인 컨트롤러 및 윈도우 관리 클래스
class MainController(QMainWindow):
    def __init__(self):
        super().__init__()

        # 1.2 서버 매니저 인스턴스 생성 및 윈도우 속성 설정
        self.ollama = ServerManager()

        # 1.0 프로그램 종료 시 서버 자동 종료 등록 (인스턴스 생성 후 등록 필수)
        atexit.register(self.ollama.stop_server)

        self.setMinimumSize(305, 655)
        self.resize(305, 655)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 1.3 중앙 컨테이너 및 내부 뷰(홈, 채팅) 인스턴스 생성
        self.container = QWidget(self)
        self.setCentralWidget(self.container)

        self.home_view = HomeView()
        self.home_view.setParent(self.container)

        self.chat_view = ChatView()
        # 1.3 컨트롤러 생성 시 뷰를 주입하지 않음 (의존성 분리)
        self.chat_logic = ChatController(self.ollama)
        self.chat_view.setParent(self.container)

        # 1.4 프론트(View)와 백(Controller)의 상호작용 연결 (Internal API)
        # 사용자가 전송 버튼 누름 -> 백엔드 로직 실행
        self.chat_view.send_btn.clicked.connect(lambda: self.chat_logic.process_message(self.chat_view.input_field.toPlainText()))
        # 백엔드 답변 도착 -> 프론트엔드에서 말풍선 추가
        self.chat_logic.answer_received.connect(lambda msg: self.chat_view.add_chat_bubble(msg, is_me=False, sender_name="Gemma"))

        # 1.4 홈 뷰 시그널(서버 구동, 채팅 전환) 연결
        self.home_view.serve_requested.connect(self.toggle_ollama_serve)
        self.home_view.chat_requested.connect(self.slide_to_chat)

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_ollama_status)
        self.status_timer.start(2000)

        # 2.1 다이내믹 아일랜드 UI 구성 및 레이아웃 설정
        self.island = QFrame(self)
        self.island.setFixedSize(120, 26)
        self.island.setStyleSheet("background-color: black; border-radius: 13px;")
        self.island.raise_()

        self.island_layout = QHBoxLayout(self.island)
        self.island_layout.setContentsMargins(6, 0, 6, 0)
        self.island_layout.setSpacing(0)

        self.back_btn = QPushButton("◁")
        self.back_btn.setFixedSize(18, 18)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #FFFFFF;
                border-radius: 9px;
                font-weight: bold;
                font-size: 10px;
                border: none;
            }
            QPushButton:hover { background-color: #555555; }
            QPushButton:pressed { background-color: #777777; }
        """)
        self.back_btn.clicked.connect(self.slide_to_home)
        self.back_btn.hide()

        self.island_layout.addWidget(self.back_btn, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.island_layout.addStretch()

        self.old_pos = None
        self.is_chat_active = False
        self.resizing = False
        self.resize_margin = 10

        self.chat_view.scroll.viewport().installEventFilter(self)

    # 3.1 창 크기 변경에 따른 내부 뷰 및 아일랜드 위치 재조정
    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        
        self.container.resize(w, h)
        self.home_view.resize(w, h)
        self.chat_view.resize(w, h)

        if self.is_chat_active:
            self.home_view.move(-w, 0)
            self.chat_view.move(0, 0)
        else:
            self.home_view.move(0, 0)
            self.chat_view.move(w, 0)

        self.island.move(int((w - self.island.width()) / 2), 8)

    # 4.1 홈에서 채팅 화면으로의 슬라이딩 전환 애니메이션
    def slide_to_chat(self):
        if self.is_chat_active: return
        self.is_chat_active = True
        self.back_btn.show()
        
        self.anim_group = QParallelAnimationGroup()
        w = self.width()
        
        anim_home = QPropertyAnimation(self.home_view, b"pos")
        anim_home.setEndValue(QPoint(-w, 0))
        anim_home.setEasingCurve(QEasingCurve.InOutQuart)
        anim_home.setDuration(450)

        anim_chat = QPropertyAnimation(self.chat_view, b"pos")
        anim_chat.setEndValue(QPoint(0, 0))
        anim_chat.setEasingCurve(QEasingCurve.InOutQuart)
        anim_chat.setDuration(450)

        self.anim_group.addAnimation(anim_home)
        self.anim_group.addAnimation(anim_chat)
        self.anim_group.start()

    # 4.2 채팅에서 홈 화면으로의 슬라이딩 전환 애니메이션
    def slide_to_home(self):
        if not self.is_chat_active: return
        self.is_chat_active = False
        self.back_btn.hide()
        
        self.anim_group = QParallelAnimationGroup()
        w = self.width()
        
        anim_home = QPropertyAnimation(self.home_view, b"pos")
        anim_home.setEndValue(QPoint(0, 0))
        anim_home.setEasingCurve(QEasingCurve.InOutQuart)
        anim_home.setDuration(450)

        anim_chat = QPropertyAnimation(self.chat_view, b"pos")
        anim_chat.setEndValue(QPoint(w, 0))
        anim_chat.setEasingCurve(QEasingCurve.InOutQuart)
        anim_chat.setDuration(450)

        self.anim_group.addAnimation(anim_home)
        self.anim_group.addAnimation(anim_chat)
        self.anim_group.start()

    # 5.1 마우스 휠 제스처를 이용한 화면 전환 이벤트 필터링
    def eventFilter(self, obj, event):
        if obj == self.chat_view.scroll.viewport() and event.type() == QEvent.Wheel:
            if self.is_chat_active and event.angleDelta().x() > 40 and abs(event.angleDelta().y()) < 20:
                self.slide_to_home()
                return True
                
        return super().eventFilter(obj, event)

    # 6.1 창 이동 및 리사이즈를 위한 마우스 클릭 지점 감지
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            # 가장자리 클릭 시 리사이즈 모드 온
            if pos.x() > self.width() - self.resize_margin or pos.y() > self.height() - self.resize_margin:
                self.resizing = True
            else:
                self.old_pos = event.globalPosition().toPoint()

    # 6.2 드래그 거리에 따른 창 크기 조절 및 위치 이동 처리
    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        is_right = pos.x() > self.width() - self.resize_margin
        is_bottom = pos.y() > self.height() - self.resize_margin

        if is_right and is_bottom: self.setCursor(Qt.SizeFDiagCursor)
        elif is_right: self.setCursor(Qt.SizeHorCursor)
        elif is_bottom: self.setCursor(Qt.SizeVerCursor)
        else: self.setCursor(Qt.ArrowCursor)
            
        if self.resizing:
            self.resize(max(self.minimumWidth(), pos.x()), max(self.minimumHeight(), pos.y()))
        elif self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.old_pos = None

    # 7.1 Ollama 서버 구동 및 중지 제어
    def toggle_ollama_serve(self):
        if not self.ollama.is_running():
            success, msg = self.ollama.start_server()
        else:
            self.ollama.stop_server()

    # 7.2 서버 상태 확인 및 홈 뷰/아일랜드 UI 동기화
    def check_ollama_status(self):
        is_active = self.ollama.is_running()

        self.home_view.update_server_status(is_active)

        if is_active:
            self.island.setStyleSheet("background-color: black; border: 1px solid #00FF00; border-radius: 13px;")
        else:
            self.island.setStyleSheet("background-color: black; border: 1px solid #FF0000; border-radius: 13px;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 터미널에서 Ctrl+C 입력 시 Python의 atexit이 동작하도록 시그널 설정
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    window = MainController()
    window.show()
    sys.exit(app.exec())