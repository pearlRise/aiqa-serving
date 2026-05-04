# projects/ollamablah/ollama/chatmain.py

class ChatController:
    def __init__(self, chat_view, ollama_manager):
        self.view = chat_view
        self.ollama = ollama_manager
        self.model_name = "gemma4:26b"
        
        # ChatView의 입력 필드와 전송 로직 연결
        # 기존 ChatView 내부의 send_message 로직을 여기서 제어하도록 가로챔
        self.view.input_field.returnPressed.disconnect() # 기존 연결 해제
        self.view.send_btn.clicked.disconnect()
        
        self.view.input_field.returnPressed.connect(self.handle_send)
        self.view.send_btn.clicked.connect(self.handle_send)

    def handle_send(self):
        text = self.view.input_field.toPlainText().strip()
        if not text:
            return
            
        # 1. 사용자 메시지 화면 출력
        self.view.add_chat_bubble(text, is_me=True)
        self.view.input_field.clear()
        
        # 2. Ollama에게 대화 요청 (일단 동기 방식, 이후 QThread 적용 권장)
        # 실제 답변을 가져오는 동안 '생각 중...' 이모지를 띄우는 연출도 가능함
        response = self.ollama.chat(self.model_name, text)
        
        # 3. AI 답변 화면 출력
        self.view.add_chat_bubble(response, is_me=False, sender_name="Gemma")