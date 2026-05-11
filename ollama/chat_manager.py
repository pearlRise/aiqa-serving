from PySide6.QtCore import QObject, Signal, QThread

# 0.1 백그라운드에서 AI 응답을 스트리밍으로 받아오는 워커 스레드
class ChatWorker(QThread):
    # 한 조각(chunk)의 텍스트가 올 때마다 발생하는 시그널
    chunk_received = Signal(str)
    # 모든 응답이 완료되었을 때 발생하는 시그널
    finished = Signal()

    def __init__(self, ollama_manager, model_name, prompt):
        super().__init__()
        self.ollama = ollama_manager
        self.model_name = model_name
        self.prompt = prompt

    def run(self):
        # 서버로부터 스트리밍 데이터 수신
        for chunk in self.ollama.chat_stream(self.model_name, self.prompt):
            self.chunk_received.emit(chunk)
        self.finished.emit()

# 1.1 채팅 화면과 AI 서버 간 상호작용 제어
class ChatController(QObject):
    # 프론트엔드에 상태 변화를 알리는 시그널들
    thinking_started = Signal()    # AI가 생각을 시작함
    chunk_delivered = Signal(str)  # 답변 조각 전달

    def __init__(self, ollama_manager):
        super().__init__()
        self.ollama = ollama_manager
        self.model_name = "gemma4:26b"
        self.worker = None

    # 2.1 사용자가 메시지를 보냈을 때 백엔드에서 처리할 로직
    def process_message(self, text):
        text = text.strip()
        if not text:
            return
            
        # AI가 이미 이전 답변을 생성(스트리밍) 중이라면 중복 실행 방지
        if self.worker and self.worker.isRunning():
            return

        # 2.2 생각 중 상태 알림 (프론트에서 {...} 버블 생성 유도)
        self.thinking_started.emit()
        
        # 2.3 워커 스레드 생성 및 실행
        self.worker = ChatWorker(self.ollama, self.model_name, text)
        self.worker.chunk_received.connect(self.chunk_delivered.emit)
        # 스레드 종료 시 메모리 해제
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()