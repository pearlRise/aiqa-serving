#============================================================
# - subject: ollama_chat_worker.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Background worker for async Ollama chat streaming.
# - caution: Safely handle thread cancellation to avoid crashes.
#============================================================
from PySide6.QtCore import QThread, Signal
from tool.exception_logging import log_error

# Ollama 엔진에서 채팅 텍스트를 스트리밍으로 받아오는 백그라운드 워커
class OllamaChatWorker(QThread):
    chunk_received = Signal(str)
    status_flag = Signal(str, str, str)

    # 워커 초기화 및 질의(prompt) 세팅
    def __init__(self, ollama_manager, model_name, prompt):
        super().__init__()
        self.ollama = ollama_manager
        self.model_name = model_name
        self.prompt = prompt
        self.is_cancelled = False

    # 1. 서버 상태 체크 후 응답 스트리밍 수신 시작
    def run(self):
        if not self.ollama.is_running():
            log_error("Ollama server is not running")
            self.status_flag.emit("chat_worker", "exception", "Exception")
            return

        self.status_flag.emit("chat_worker", "start", "Generating...")
        try:
            # 2. 스트림 청크를 UI 뷰에 실시간 전송
            for chunk in self.ollama.chat_stream(self.model_name, self.prompt):
                if self.is_cancelled:
                    self.status_flag.emit("chat_worker", "end", "Stopped")
                    return
                self.chunk_received.emit(chunk)
            self.status_flag.emit("chat_worker", "end", "Generated")
        except Exception as e:
            # 연결 끊김, 모델 언로드 등 스트리밍 중 예외 처리
            log_error("Ollama streaming error", e)
            self.status_flag.emit("chat_worker", "exception", "Exception")