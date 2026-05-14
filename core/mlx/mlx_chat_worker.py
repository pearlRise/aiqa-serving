#============================================================
# - subject: mlx_chat_worker.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Background worker for async MLX chat streaming.
# - caution: Safely handle thread cancellation to avoid crashes.
#============================================================
from PySide6.QtCore import QThread, Signal

# MLX 엔진에서 채팅 텍스트를 스트리밍으로 받아오는 백그라운드 워커
class MlxChatWorker(QThread):
    chunk_received = Signal(str)
    status_flag = Signal(str, str, str)

    def __init__(self, mlx_manager, prompt):
        super().__init__()
        self.mlx = mlx_manager
        self.prompt = prompt
        self.is_cancelled = False

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
                if self.is_cancelled:
                    self.status_flag.emit("chat_worker", "end", "Stopped")
                    return
                self.chunk_received.emit(chunk)
            self.status_flag.emit("chat_worker", "end", "Generated")
        except Exception as e:
            # MLX 모델 메모리 부족 또는 추론 중 예외 처리
            print(f"MlxChatWorker Error: {e}")
            self.status_flag.emit("chat_worker", "exception", "Exception")