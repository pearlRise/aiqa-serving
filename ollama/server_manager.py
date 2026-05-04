import subprocess
import requests
import os
import signal

class ServerManager:
    def __init__(self):
        self.api_base = "http://localhost:11434/api"
        self.process = None

    # [백엔드 제어] 서버 프로세스 구동
    def start_server(self):
        if self.is_running():
            return True, "is_running: True"
        
        try:
            # shell=False로 설정하고 리스트 형태로 명령어를 전달하는 게 보안상 더 안전해.
            self.process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL, # 로그는 나중에 파일이나 큐로 관리하자
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid # Mac/Linux에서 자식 프로세스 그룹 제어를 위해 필요
            )
            return True, "Run Ollama Server..."
        except Exception as e:
            return False, f"Fail to run server: {str(e)}"

    # [프론트엔드 통신] 서버 상태 확인 (API 호출 방식)
    def is_running(self):
        try:
            # 단순 프로세스 체크보다 API 응답을 확인하는 게 더 정확해.
            response = requests.get(f"{self.api_base}/tags", timeout=1)
            return response.status_code == 200
        except:
            return False

    # [백엔드 제어] 서버 프로세스 종료
    def stop_server(self):
        if self.process:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process = None
            return True
        return False