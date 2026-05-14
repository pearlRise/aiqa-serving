#============================================================
# - subject: mlx_model_worker.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Background worker for async MLX model operations.
# - caution: Safely handle thread cancellation to avoid crashes.
#============================================================
from PySide6.QtCore import QThread, Signal

# MLX 모델 로드 및 언로드를 비동기로 처리하는 백그라운드 워커
class MlxModelWorker(QThread):
    finished = Signal()
    status_flag = Signal(str, str, str)

    # MLX 워커 초기화 및 대상 모델 설정
    def __init__(self, mlx_manager, action, target_model):
        super().__init__()
        self.mlx = mlx_manager
        self.action = action
        self.target_model = target_model
        self.is_cancelled = False

    # 워커 실행: MLX 모델의 로드/언로드 동작 수행
    def run(self):
        try:
            # 1. 로드: MLX 모델 로드 및 취소 시 언로드 롤백
            if self.action == 'load':
                self.status_flag.emit("mlx_model_worker", "start", "Loading...")
                self.mlx.load_model(self.target_model)
                if self.is_cancelled:
                    self.mlx.unload_model()
                    self.status_flag.emit("mlx_model_worker", "end", "Cancelled")
                else:
                    self.status_flag.emit("mlx_model_worker", "end", "Loaded")
            # 2. 언로드: MLX 모델 언로드
            elif self.action == 'unload':
                self.status_flag.emit("mlx_model_worker", "start", "Unloading...")
                self.mlx.unload_model()
                self.status_flag.emit("mlx_model_worker", "end", "Unloaded")
        except Exception as e:
            # MLX 작업 중 발생한 예외 처리 및 UI 예외 상태 전송
            print(f"MlxModelWorker Error: {e}")
            self.status_flag.emit("mlx_model_worker", "exception", "Exception")
            
        self.finished.emit()