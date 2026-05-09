from PySide6.QtCore import QObject, Signal

# 1.1 채팅 화면과 AI 서버 간 상호작용 제어
class ChatController(QObject):
    # 1.2 프론트엔드(View)로 전달할 데이터 정의 (내부 API 역할)
    answer_received = Signal(str)  # AI 응답이 도착했을 때 발생하는 시그널

    def __init__(self, ollama_manager):
        super().__init__()
        self.ollama = ollama_manager
        self.model_name = "gemma4:26b"

    # 2.1 사용자가 메시지를 보냈을 때 백엔드에서 처리할 로직
    def process_message(self, text):
        """
        프론트엔드로부터 텍스트를 전달받아 AI 서버와 통신하고 결과를 알림
        """
        text = text.strip()
        if not text:
            return

        # Ollama API를 통한 AI 답변 획득
        response = self.ollama.chat(self.model_name, text)
        
        # 결과를 시그널로 전달 (View는 이 시그널을 구독해서 화면을 갱신)
        self.answer_received.emit(response)