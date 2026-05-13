import subprocess
import requests
import os
import signal
import json

class ServerManager:
    def __init__(self):
        self.api_base = "http://localhost:11434/api"
        self.process = None
        self.active_model = None

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

    def is_running(self):
        try:
            response = requests.get(f"{self.api_base}/tags", timeout=1)
            return response.status_code == 200
        except:
            return False

    def stop_server(self):
        if self.active_model:
            self.unload_model(self.active_model)
            
        killed = False
        if self.process:
            try:
                pgid = os.getpgid(self.process.pid)
                os.killpg(pgid, signal.SIGTERM)
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
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
                subprocess.run(["pkill", "ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
                
        return True

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

    def chat_stream(self, model_name, prompt):
        try:
            url = f"{self.api_base}/generate"
            data = {
                "model": model_name,
                "prompt": prompt,
                "stream": True 
            }
            with requests.post(url, json=data, timeout=30, stream=True) as response:
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode("utf-8"))
                        yield chunk.get("response", "")
                        if chunk.get("done"):
                            break
        except requests.exceptions.ConnectionError as e:
            print(f"Ollama ConnectionError: {e}")
        except Exception as e:
            print(f"Ollama Chat Stream Error: {e}")