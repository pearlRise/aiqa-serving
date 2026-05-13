from PySide6.QtCore import QObject, Signal, QThread

class ChatWorker(QThread):
    chunk_received = Signal(str)
    status_flag = Signal(str, str, str)

    def __init__(self, ollama_manager, model_name, prompt):
        super().__init__()
        self.ollama = ollama_manager
        self.model_name = model_name
        self.prompt = prompt

    def run(self):
        if not self.ollama.is_running():
            print("ChatWorker Error: Ollama server is not running.")
            self.status_flag.emit("chat_worker", "exception", "Exception")
            return

        self.status_flag.emit("chat_worker", "start", "Generating...")
        try:
            for chunk in self.ollama.chat_stream(self.model_name, self.prompt):
                self.chunk_received.emit(chunk)
            self.status_flag.emit("chat_worker", "end", "Generated")
        except Exception as e:
            print(f"ChatWorker Error: {e}")
            self.status_flag.emit("chat_worker", "exception", "Exception")

class MlxChatWorker(QThread):
    chunk_received = Signal(str)
    status_flag = Signal(str, str, str)

    def __init__(self, mlx_manager, prompt):
        super().__init__()
        self.mlx = mlx_manager
        self.prompt = prompt

    def run(self):
        if not self.mlx.active_model:
            print("MlxChatWorker Error: MLX model is not loaded.")
            self.status_flag.emit("chat_worker", "exception", "Exception")
            return

        self.status_flag.emit("chat_worker", "start", "Generating...")
        try:
            for chunk in self.mlx.chat_stream(self.prompt):
                self.chunk_received.emit(chunk)
            self.status_flag.emit("chat_worker", "end", "Generated")
        except Exception as e:
            print(f"MlxChatWorker Error: {e}")
            self.status_flag.emit("chat_worker", "exception", "Exception")

class ChatController(QObject):
    thinking_started = Signal()
    chunk_delivered = Signal(str)
    status_flag = Signal(str, str, str)

    def __init__(self, ollama_manager, mlx_manager=None):
        super().__init__()
        self.ollama = ollama_manager
        self.mlx = mlx_manager
        self.worker = None

    def process_message(self, text, engine="Ollama"):
        text = text.strip()
        if not text:
            return
            
        if self.worker and self.worker.isRunning():
            return

        self.thinking_started.emit()
        
        if engine == "Ollama":
            if not self.ollama.active_model:
                print("ChatController Error: No Ollama model selected.")
                return
            self.worker = ChatWorker(self.ollama, self.ollama.active_model, text)
        else:
            if not self.mlx or not self.mlx.active_model:
                print("ChatController Error: No MLX model selected.")
                return
            self.worker = MlxChatWorker(self.mlx, text)

        self.worker.chunk_received.connect(self.chunk_delivered.emit)
        self.worker.status_flag.connect(self.status_flag.emit)
        self.worker.finished.connect(self._cleanup_worker)
        self.worker.start()

    def _cleanup_worker(self):
        if self.worker:
            self.worker.deleteLater()
            self.worker = None