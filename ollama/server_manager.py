import subprocess
import requests
import os
import signal
import json

# 1.1 Ollama API 경로 및 프로세스 상태 초기화
class ServerManager:
    def __init__(self):
        self.api_base = "http://localhost:11434/api"
        self.process = None
        self.active_model = None

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
        # 프로세스 종료 전 메모리에 적재된 모델을 먼저 해제
        if self.active_model:
            self.unload_model(self.active_model)
            
        killed = False
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
                killed = True
            except ProcessLookupError:
                # 이미 프로세스가 종료된 경우 무시
                pass
            except Exception as e:
                print(f"Error while stopping server: {e}")
            finally:
                self.process = None
        
        # 앱 외부에서 백그라운드로 켜진 서버이거나, 덜 닫힌 경우 강제 종료 시도
        if not killed or self.is_running():
            try:
                subprocess.run(["pkill", "ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
                
        return True

    # 3.2 로컬에 설치된 모델 리스트 조회
    def get_local_models(self):
        if not self.is_running():
            return []
        try:
            response = requests.get(f"{self.api_base}/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            return []
        except requests.exceptions.RequestException:
            return []

    # 3.3 지정한 모델을 메모리에 적재
    def load_model(self, model_name):
        if not self.is_running(): return False
        # 다른 모델이 이미 적재되어 있다면 먼저 해제
        if self.active_model and self.active_model != model_name:
            self.unload_model(self.active_model)
        try:
            # 빈 프롬프트를 전송해야 실제 모델이 메모리에 적재됨 (Ollama API 스펙)
            # 모델 로딩 시간에 맞게 타임아웃을 넉넉히(120초) 부여
            requests.post(f"{self.api_base}/generate", json={"model": model_name, "prompt": "", "keep_alive": -1}, timeout=120)
            self.active_model = model_name
            return True
        except Exception:
            return False

    # 3.4 지정한 모델(또는 현재 활성화된 모델)을 메모리에서 해제
    def unload_model(self, model_name=None):
        if not self.is_running(): return False
        model_to_unload = model_name or self.active_model
        if not model_to_unload: return True
        try:
            # 모델 해제 시에도 빈 프롬프트를 함께 전송
            requests.post(f"{self.api_base}/generate", json={"model": model_to_unload, "prompt": "", "keep_alive": 0}, timeout=10)
            if self.active_model == model_to_unload:
                self.active_model = None
            return True
        except Exception:
            return False

    # 4.1 AI 모델 대화 요청 및 스트리밍 응답 제너레이터
    def chat_stream(self, model_name, prompt):
        try:
            url = f"{self.api_base}/generate"
            data = {
                "model": model_name,
                "prompt": prompt,
                "stream": True 
            }
            # stream=True 옵션으로 요청
            with requests.post(url, json=data, timeout=30, stream=True) as response:
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode("utf-8"))
                        yield chunk.get("response", "")
                        if chunk.get("done"):
                            break
        except requests.exceptions.ConnectionError:
            yield "please run the server first 😁"
        except Exception as e:
            yield f"Connection Failed: {str(e)}"