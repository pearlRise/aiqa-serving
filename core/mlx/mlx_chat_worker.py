#============================================================
# - subject: mlx_chat_worker.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Background worker for async MLX chat streaming.
# - caution: Safely handle thread cancellation to avoid crashes.
#============================================================
from PySide6.QtCore import QThread, Signal
from tool.exception_logging import log_error

class MlxChatWorker(QThread):
    chunk_received = Signal(str)
    status_flag = Signal(str, str, str)

    def __init__(self, mlx_manager, prompt):
        super().__init__()
        self.mlx = mlx_manager
        self.prompt = prompt
        self.is_cancelled = False

    def run(self):
        if not self.mlx.active_model:
            log_error("MLX model is not loaded")
            self.status_flag.emit("chat_worker", "exception", "Exception")
            return

        self.status_flag.emit("chat_worker", "start", "Generating...")
        try:
            for chunk in self.mlx.chat_stream(self.prompt):
                if self.is_cancelled:
                    self.status_flag.emit("chat_worker", "end", "Stopped")
                    return
                self.chunk_received.emit(chunk)
            self.status_flag.emit("chat_worker", "end", "Generated")
        except Exception as e:
            log_error("Chat stream inference failed", e)
            self.status_flag.emit("chat_worker", "exception", "Exception")