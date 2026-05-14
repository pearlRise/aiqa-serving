#============================================================
# - subject: chat_controller.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Manages chat requests for Ollama and MLX.
# - caution: Ensure QThread safety when streaming chunks.
#============================================================
from PySide6.QtCore import QObject, Signal
from core.ollama.ollama_chat_worker import OllamaChatWorker
from core.mlx.mlx_chat_worker import MlxChatWorker

# 채팅 입력과 엔진(Ollama/MLX) 간의 처리를 중재하는 컨트롤러
class ChatController(QObject):
    thinking_started = Signal()
    chunk_delivered = Signal(str)
    status_flag = Signal(str, str, str)

    # 컨트롤러 초기화 및 매니저 의존성 주입
    def __init__(self, ollama_manager, mlx_manager=None):
        super().__init__()
        self.ollama = ollama_manager
        self.mlx = mlx_manager
        # 현재 동작 중인 스트리밍 워커 추적 변수
        self.worker = None

    # 텍스트 검증 후 현재 설정된 엔진에 맞게 채팅 워커 실행
    def process_message(self, text, engine="Ollama"):
        text = text.strip()
        if not text:
            return
            
        if self.worker and self.worker.isRunning():
            return

        self.thinking_started.emit()
        
        # 1. Ollama 엔진이 선택된 경우 Ollama 워커 초기화
        if engine == "Ollama":
            if not self.ollama.active_model:
                print("ChatController Error: No Ollama model selected.")
                return
            self.worker = OllamaChatWorker(self.ollama, self.ollama.active_model, text)
        else:
            # 2. MLX 엔진이 선택된 경우 MLX 워커 초기화
            if not self.mlx or not self.mlx.active_model:
                print("ChatController Error: No MLX model selected.")
                return
            self.worker = MlxChatWorker(self.mlx, text)

        # 워커 시그널 연결 및 작업 시작
        self.worker.chunk_received.connect(self.chunk_delivered.emit)
        self.worker.status_flag.connect(self.status_flag.emit)
        self.worker.finished.connect(self._cleanup_worker)
        self.worker.start()

    # 이전 스트리밍 워커가 남긴 메모리 점유 안전 해제
    def _cleanup_worker(self):
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    # 진행 중인 채팅 생성 작업을 취소
    def cancel_generation(self):
        if self.worker and self.worker.isRunning():
            self.worker.is_cancelled = True