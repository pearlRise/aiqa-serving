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
            self.chunk_received.emit("🧐 Please run server first!")
            self.status_flag.emit("chat_worker", "exception", "Exception")
            return

        self.status_flag.emit("chat_worker", "start", "Generating...")
        try:
            for chunk in self.ollama.chat_stream(self.model_name, self.prompt):
                self.chunk_received.emit(chunk)
            self.status_flag.emit("chat_worker", "end", "Generated")
        except Exception as e:
            self.status_flag.emit("chat_worker", "exception", "Exception")

class ChatController(QObject):
    thinking_started = Signal()
    chunk_delivered = Signal(str)
    status_flag = Signal(str, str, str)

    def __init__(self, ollama_manager):
        super().__init__()
        self.ollama = ollama_manager
        self.worker = None

    def process_message(self, text):
        text = text.strip()
        if not text:
            return
            
        if self.worker and self.worker.isRunning():
            return

        if not self.ollama.active_model:
            self.chunk_delivered.emit("🧐 Please choose a model from the 'Choose Model' menu first!")
            return

        self.thinking_started.emit()
        
        self.worker = ChatWorker(self.ollama, self.ollama.active_model, text)
        self.worker.chunk_received.connect(self.chunk_delivered.emit)
        self.worker.status_flag.connect(self.status_flag.emit)
        self.worker.finished.connect(self._cleanup_worker)
        self.worker.start()

    def _cleanup_worker(self):
        if self.worker:
            self.worker.deleteLater()
            self.worker = None