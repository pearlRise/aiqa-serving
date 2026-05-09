import subprocess
import requests
import os
import signal

# 1.1 Ollama API 경로 및 프로세스 상태 초기화
class ServerManager:
    def __init__(self):
        self.api_base = "http://localhost:11434/api"
        self.process = None

    # 1.2 Ollama 서버 프로세스 백그라운드 실행
    def start_server(self):
        try:
            if self.is_running():
                return True, "Ollama server is already running."

            self.process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid
            )
            return True, "Run Ollama Server..."
        except Exception as e:
            return False, f"Fail to run server: {str(e)}"

    # 2.1 API 호출을 통한 실시간 서버 가동 상태 확인
    def is_running(self):
        try:
            response = requests.get(f"{self.api_base}/tags", timeout=1)
            return response.status_code == 200
        except:
            return False

    # 3.1 실행 중인 서버 프로세스 강제 종료
    def stop_server(self):
        if self.process:
            try:
                # 프로세스 그룹 전체에 종료 신호 전송
                pgid = os.getpgid(self.process.pid)
                os.killpg(pgid, signal.SIGTERM)
                # 프로세스가 완전히 종료될 때까지 최대 2초 대기
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                # 이미 프로세스가 종료된 경우 무시
                pass
            except Exception as e:
                print(f"Error while stopping server: {e}")
            finally:
                self.process = None
            
            return True
        return False
    
    # 4.1 AI 모델 대화 요청 및 응답 데이터 처리
    def chat(self, model_name, prompt):
        try:
            url = f"{self.api_base}/generate"
            data = {
                "model": model_name,
                "prompt": prompt,
                "stream": False 
            }
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"Connection Failed: {str(e)}"