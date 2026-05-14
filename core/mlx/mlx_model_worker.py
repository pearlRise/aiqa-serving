#============================================================
# - subject: mlx_model_worker.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Background worker for async MLX model operations.
# - caution: Safely handle thread cancellation to avoid crashes.
#============================================================
from PySide6.QtCore import QThread, Signal
from tool.exception_logging import log_error

class MlxModelWorker(QThread):
    finished = Signal()
    status_flag = Signal(str, str, str)

    def __init__(self, mlx_manager, action, target_model):
        super().__init__()
        self.mlx = mlx_manager
        self.action = action
        self.target_model = target_model
        self.is_cancelled = False

    def run(self):
        try:
            if self.action == 'load':
                self.status_flag.emit("mlx_model_worker", "start", "Loading...")
                self.mlx.load_model(self.target_model)
                if self.is_cancelled:
                    self.mlx.unload_model()
                    self.status_flag.emit("mlx_model_worker", "end", "Cancelled")
                else:
                    self.status_flag.emit("mlx_model_worker", "end", "Loaded")
            elif self.action == 'unload':
                self.status_flag.emit("mlx_model_worker", "start", "Unloading...")
                self.mlx.unload_model()
                self.status_flag.emit("mlx_model_worker", "end", "Unloaded")
        except Exception as e:
            log_error("MLX model operation failed", e)
            self.status_flag.emit("mlx_model_worker", "exception", "Exception")
            
        self.finished.emit()