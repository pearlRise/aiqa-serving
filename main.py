#============================================================
# - subject: main.py
# - created: 2026-05-13
# - updated: 2026-05-14
# - summary: Main entry point for starting the application.
# - caution: None.
#============================================================
import sys
import os
import signal

# 패키지 충돌 방지용 절대 경로 지정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PySide6.QtWidgets import QApplication
from core.app_controller import AppController

# 애플리케이션 진입 지점
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 터미널 Ctrl+C 로 앱을 정상 종료하기 위한 시그널 핸들러 설정
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    controller = AppController()
    controller.window.show()
    sys.exit(app.exec())