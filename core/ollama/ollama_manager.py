#============================================================
# - subject: ollama_manager.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Controls Ollama local server and API processes.
# - caution: Carefully handle subprocess termination.
#============================================================
import subprocess
import requests
import os
import signal
import json

# Ollama의 프로세스 생명주기 및 API 통신을 전담하는 매니저
class ServerManager:
    # Ollama 로컬 호스트 API 주소와 상태 추적 변수 초기화
    def __init__(self):
        self.api_base = "http://localhost:11434/api"
        # 실행된 프로세스 객체 (SIGTERM 전송용)
        self.process = None
        # 현재 메모리에 로드된 Ollama 모델명
        self.active_model = None

    # 서브프로세스로 'ollama serve'를 실행하여 백그라운드 서버 구동
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

    # API 상태를 호출하여 서버가 정상 응답하는지 핑 체크
    def is_running(self):
        try:
            response = requests.get(f"{self.api_base}/tags", timeout=1)
            return response.status_code == 200
        except:
            return False

    # Ollama 프로세스 그룹 강제 종료 로직 (atexit 등에 의해 호출)
    def stop_server(self):
        # 1. 종료 전 로드된 모델 메모리 반환
        if self.active_model:
            self.unload_model(self.active_model)
            
        killed = False
        if self.process:
            try:
                # 2. 프로세스 그룹 ID 획득 후 SIGTERM 전송
                pgid = os.getpgid(self.process.pid)
                os.killpg(pgid, signal.SIGTERM)
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # 응답이 없으면 SIGKILL로 강제 킬
                    os.killpg(pgid, signal.SIGKILL)
                killed = True
            except ProcessLookupError:
                pass
            except Exception as e:
                print(f"Error while stopping server: {e}")
            finally:
                self.process = None
        
        if not killed or self.is_running():
            try:
                # 3. 최후 수단으로 pkill 시스템 명령어 실행
                subprocess.run(["pkill", "ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
                
        return True

    # 로컬 디렉토리에 설치된 Ollama 모델 리스트를 API로 획득
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

    # API를 이용해 선택된 모델을 메모리에 로드
    def load_model(self, model_name):
        if not self.is_running(): return False
        if self.active_model and self.active_model != model_name:
            self.unload_model(self.active_model)
        try:
            requests.post(f"{self.api_base}/generate", json={"model": model_name, "prompt": "", "keep_alive": -1}, timeout=120)
            self.active_model = model_name
            return True
        except Exception:
            return False

    # 특정 모델(기본값은 활성화 모델)을 메모리에서 언로드
    def unload_model(self, model_name=None):
        if not self.is_running(): return False
        model_to_unload = model_name or self.active_model
        if not model_to_unload: return True
        try:
            requests.post(f"{self.api_base}/generate", json={"model": model_to_unload, "prompt": "", "keep_alive": 0}, timeout=10)
            if self.active_model == model_to_unload:
                self.active_model = None
            return True
        except Exception:
            return False

    # 스트리밍 방식(stream=True)으로 프롬프트를 전송하고 텍스트 조각을 yield
    def chat_stream(self, model_name, prompt):
        try:
            url = f"{self.api_base}/generate"
            data = {
                "model": model_name,
                "prompt": prompt,
                "stream": True 
            }
            with requests.post(url, json=data, timeout=30, stream=True) as response:
                # 청크 디코딩 후 response 필드만 추출
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode("utf-8"))
                        yield chunk.get("response", "")
                        if chunk.get("done"):
                            break
        except requests.exceptions.ConnectionError as e:
            # 통신 오류 시 프로세스 강제 종료 대비 예외 처리
            print(f"Ollama ConnectionError: {e}")
        except Exception as e:
            print(f"Ollama Chat Stream Error: {e}")