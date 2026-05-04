import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from ollama.server_manager import ServerManager
from ollama.chat_manager import ChatController

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QFrame, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QPoint, QEvent, QTimer

from view.view_home_interface import HomeView
from view.view_chat_interface import ChatView

class MainController(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. 매니저 인스턴스 생성
        self.ollama = ServerManager()

        # 2. 윈도우 기본 설정
        self.setMinimumSize(305, 655)
        self.resize(305, 655)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 3. 중앙 컨테이너 및 뷰(View) 인스턴스 먼저 생성 ★ (이게 위로 올라와야 함)
        self.container = QWidget(self)
        self.setCentralWidget(self.container)

        self.home_view = HomeView()
        self.home_view.setParent(self.container)

        self.chat_view = ChatView()
        self.chat_logic = ChatController(self.chat_view, self.ollama)
        self.chat_view.setParent(self.container)

        # 4. 이제 객체가 존재하므로 시그널들을 연결 ★
        self.home_view.serve_requested.connect(self.toggle_ollama_serve)
        self.home_view.chat_requested.connect(self.slide_to_chat)

        # 5. 상태 모니터링 타이머 시작
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_ollama_status)
        self.status_timer.start(2000)

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

        # 상태 및 리사이즈 제어용 변수
        self.old_pos = None
        self.is_chat_active = False
        self.resizing = False
        self.resize_margin = 10

        self.chat_view.scroll.viewport().installEventFilter(self)
        
    # [신규] 창 크기가 변할 때 내부 뷰와 아일랜드 위치를 재조정하는 사령탑
    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        
        self.container.resize(w, h)
        self.home_view.resize(w, h)
        self.chat_view.resize(w, h)

        # 창 크기가 변해도 현재 보고 있는 화면에 맞춰 x좌표를 계속 보정해줌
        if self.is_chat_active:
            self.home_view.move(-w, 0)
            self.chat_view.move(0, 0)
        else:
            self.home_view.move(0, 0)
            self.chat_view.move(w, 0)

        self.island.move(int((w - self.island.width()) / 2), 8)

    # [수정] 고정값 305 대신 self.width()를 활용한 유동적 슬라이딩
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

    # 7. 제스처 및 드래그 이벤트
    def eventFilter(self, obj, event):
        # 감지된 객체가 chat_view의 뷰포트인지 정확히 확인
        if obj == self.chat_view.scroll.viewport() and event.type() == QEvent.Wheel:
            # 채팅창이 열려있을 때, 우측 스와이프(x축 이동량) 감지
            if self.is_chat_active and event.angleDelta().x() > 40 and abs(event.angleDelta().y()) < 20:
                self.slide_to_home()
                return True # 이벤트 소모 (스크롤이 튀는 현상 방지)
                
        return super().eventFilter(obj, event)

    # [수정] 모서리 인식 및 리사이즈 로직 부활
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            # 가장자리 클릭 시 리사이즈 모드 온
            if pos.x() > self.width() - self.resize_margin or pos.y() > self.height() - self.resize_margin:
                self.resizing = True
            else:
                self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        is_right = pos.x() > self.width() - self.resize_margin
        is_bottom = pos.y() > self.height() - self.resize_margin
        
        # 커서 아이콘 변경
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

    def toggle_ollama_serve(self):
        if not self.ollama.is_running():
            success, msg = self.ollama.start_server()
            # 다이내믹 아일랜드나 로그 창에 msg 출력 로직 추가 가능
        else:
            self.ollama.stop_server()

    # [상태 동기화] 타이머에 의해 주기적으로 실행
    def check_ollama_status(self):
        is_active = self.ollama.is_running()
        
        # 홈 뷰의 대시보드 데이터를 실시간으로 업데이트
        # (HomeView에 status 업데이트 메서드를 미리 만들어두면 편해)
        self.home_view.update_server_status(is_active)
        
        # 다이내믹 아일랜드에 작은 점 하나 찍어주는 연출도 좋겠지?
        if is_active:
            self.island.setStyleSheet("background-color: black; border: 1px solid #00FF00; border-radius: 13px;")
        else:
            self.island.setStyleSheet("background-color: black; border: 1px solid #FF0000; border-radius: 13px;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainController()
    window.show()
    sys.exit(app.exec())