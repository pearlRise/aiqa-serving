#============================================================
# - subject: chat_controller.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Manages chat requests for Ollama and MLX.
# - caution: Ensure QThread safety when streaming chunks.
#============================================================
from PySide6.QtCore import QObject, Signal, QThread

# Ollama 엔진에서 채팅 텍스트를 스트리밍으로 받아오는 백그라운드 워커
class ChatWorker(QThread):
    chunk_received = Signal(str)
    status_flag = Signal(str, str, str)

    # 워커 초기화 및 질의(prompt) 세팅
    def __init__(self, ollama_manager, model_name, prompt):
        super().__init__()
        self.ollama = ollama_manager
        self.model_name = model_name
        self.prompt = prompt

    # 1. 서버 상태 체크 후 응답 스트리밍 수신 시작
    def run(self):
        if not self.ollama.is_running():
            print("ChatWorker Error: Ollama server is not running.")
            self.status_flag.emit("chat_worker", "exception", "Exception")
            return

        self.status_flag.emit("chat_worker", "start", "Generating...")
        try:
            # 2. 스트림 청크를 UI 뷰에 실시간 전송
            for chunk in self.ollama.chat_stream(self.model_name, self.prompt):
                self.chunk_received.emit(chunk)
            self.status_flag.emit("chat_worker", "end", "Generated")
        except Exception as e:
            # 연결 끊김, 모델 언로드 등 스트리밍 중 예외 처리
            print(f"ChatWorker Error: {e}")
            self.status_flag.emit("chat_worker", "exception", "Exception")

# MLX 엔진에서 채팅 텍스트를 스트리밍으로 받아오는 백그라운드 워커
class MlxChatWorker(QThread):
    chunk_received = Signal(str)
    status_flag = Signal(str, str, str)

    def __init__(self, mlx_manager, prompt):
        super().__init__()
        self.mlx = mlx_manager
        self.prompt = prompt

    # 1. 모델 로드 상태 체크 후 응답 스트리밍 수신 시작
    def run(self):
        if not self.mlx.active_model:
            print("MlxChatWorker Error: MLX model is not loaded.")
            self.status_flag.emit("chat_worker", "exception", "Exception")
            return

        self.status_flag.emit("chat_worker", "start", "Generating...")
        try:
            # 2. MLX 스트림 청크를 UI 뷰에 실시간 전송
            for chunk in self.mlx.chat_stream(self.prompt):
                self.chunk_received.emit(chunk)
            self.status_flag.emit("chat_worker", "end", "Generated")
        except Exception as e:
            # MLX 모델 메모리 부족 또는 추론 중 예외 처리
            print(f"MlxChatWorker Error: {e}")
            self.status_flag.emit("chat_worker", "exception", "Exception")

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
            self.worker = ChatWorker(self.ollama, self.ollama.active_model, text)
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