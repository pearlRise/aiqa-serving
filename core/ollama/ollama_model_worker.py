#============================================================
# - subject: ollama_model_worker.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Background worker for async Ollama model operations.
# - caution: Safely handle thread cancellation to avoid crashes.
#============================================================
from PySide6.QtCore import QThread, Signal
from core.exception_logging import log_error

# Ollama 모델 로드, 언로드, 스위칭을 비동기로 처리하는 백그라운드 워커
class OllamaModelWorker(QThread):
    finished = Signal()
    status_flag = Signal(str, str, str)

    # 워커 초기화 및 대상 모델 설정
    def __init__(self, ollama_manager, action, target_model, current_model=None):
        super().__init__()
        self.ollama = ollama_manager
        self.action = action
        self.target_model = target_model
        self.current_model = current_model
        self.is_cancelled = False

    # 워커 실행: action 값에 따라 비동기로 모델 상태 변경 처리
    def run(self):
        try:
            # 1. 스위칭: 기존 모델 언로드 후 새 모델 로드
            if self.action == 'switch':
                if self.current_model:
                    self.status_flag.emit("ollama_model_worker", "start", "Unloading...")
                    self.ollama.unload_model(self.current_model)
                if not self.is_cancelled:
                    self.status_flag.emit("ollama_model_worker", "start", "Loading...")
                    self.ollama.load_model(self.target_model)
                if self.is_cancelled:
                    self.ollama.unload_model(self.target_model)
                    self.status_flag.emit("ollama_model_worker", "end", "Cancelled")
                else:
                    self.status_flag.emit("ollama_model_worker", "end", "Loaded")

            # 2. 로드: 새 모델 로드
            elif self.action == 'load':
                self.status_flag.emit("ollama_model_worker", "start", "Loading...")
                self.ollama.load_model(self.target_model)
                if self.is_cancelled:
                    self.ollama.unload_model(self.target_model)
                    self.status_flag.emit("ollama_model_worker", "end", "Cancelled")
                else:
                    self.status_flag.emit("ollama_model_worker", "end", "Loaded")

            # 3. 언로드: 현재 모델 언로드
            elif self.action == 'unload':
                self.status_flag.emit("ollama_model_worker", "start", "Unloading...")
                self.ollama.unload_model(self.target_model)
                self.status_flag.emit("ollama_model_worker", "end", "Unloaded")
        except Exception as e:
            # 모델 작업 중 발생한 예외 처리 및 UI 예외 상태 전송
            log_error("Ollama model operation failed", e)
            self.status_flag.emit("ollama_model_worker", "exception", "Exception")
            
        self.finished.emit()