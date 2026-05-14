#============================================================
# - subject: mlx_manager.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Apple MLX framework based LLM model controller and text stream manager.
# - caution: Ensure proper memory management when loading/unloading models.
#============================================================
import os
from tool.exception_logging import log_error
from tool.evaluation_tps import TPSMeter

# Apple MLX 프레임워크 기반 LLM 모델 제어 및 텍스트 스트림 매니저
class MlxManager:
    def __init__(self):
        self.model = None
        self.processor = None
        self.active_model = None
        self.drafter = None
        self.draft_kind = None

    def load_model(self, model_name):
        try:
            import mlx.core as mx
            import mlx_vlm
        except ImportError as e:
            log_error("Failed to import mlx_vlm modules", e)
            raise

        base_model_path = os.path.join("models", "mlx", model_name)
        if not os.path.isdir(base_model_path):
            log_error("Model directory not found", Exception(base_model_path))
            raise FileNotFoundError(base_model_path)

        actual_model_path = base_model_path
        if not os.path.exists(os.path.join(actual_model_path, 'config.json')):
            found = False
            for root, dirs, files in os.walk(base_model_path):
                if 'config.json' in files:
                    actual_model_path = root
                    found = True
                    break
            if not found:
                raise FileNotFoundError("config.json not found in model path")
        
        self.model, self.processor = mlx_vlm.load(actual_model_path)
        mx.eval(self.model)
        self.active_model = model_name
        
        # --- Drafter (Speculative Decoding) 로드 로직 ---
        # 경로 탐색 로직을 제거하고, gemma-4 모델 계열에 대해 특정 어시스턴트 모델 경로를 하드코딩합니다.
        base_assistant_path = os.path.join("models", "mlx", "models--mlx-community--gemma-4-26B-A4B-it-assistant-bf16")
        print(f"🔍 [MLX-VLM] Checking drafter path: {os.path.abspath(base_assistant_path)}", flush=True)

        if os.path.exists(base_assistant_path) and "gemma-4" in model_name.lower():
            # HF 캐시 구조(blobs, snapshots 등)를 대비하여 config.json이 있는 실제 경로를 탐색합니다.
            actual_assistant_path = base_assistant_path
            if not os.path.exists(os.path.join(actual_assistant_path, 'config.json')):
                for root, dirs, files in os.walk(base_assistant_path):
                    if 'config.json' in files:
                        actual_assistant_path = root
                        break

            try:
                from mlx_vlm.speculative.drafters import load_drafter
                self.draft_kind = "mtp" # gemma-4는 mtp 사용
                
                loaded_drafter = load_drafter(actual_assistant_path, kind=self.draft_kind)
                # load_drafter가 (model, processor) 형태의 튜플을 반환할 수 있으므로, 모델 객체만 안전하게 추출합니다.
                self.drafter = loaded_drafter[0] if isinstance(loaded_drafter, tuple) else loaded_drafter
                
                mx.eval(self.drafter)
                print(f"🚀 [MLX-VLM] Drafter ({self.draft_kind}) loaded from {actual_assistant_path}", flush=True)
            except Exception as e:
                log_error("Failed to load drafter model", e)
        else:
            print(f"⚠️ [MLX-VLM] Drafter condition failed. Path exists: {os.path.exists(base_assistant_path)}, 'gemma-4' in model_name: {'gemma-4' in model_name.lower()}", flush=True)

        return True

    def unload_model(self):
        self.model = None
        self.processor = None
        self.active_model = None
        self.drafter = None
        self.draft_kind = None
        return True

    def chat_stream(self, prompt_text):
        try:
            import mlx.core as mx
            from mlx_vlm.generate import stream_generate
            from mlx_vlm.prompt_utils import apply_chat_template

            mx.eval(self.model)
            
            prompt = apply_chat_template(
                self.processor,
                self.model.config,
                prompt_text
            )

            generate_kwargs = {
                "model": self.model, 
                "processor": self.processor, 
                "prompt": prompt,
                "max_tokens": 1024
            }

            if self.drafter:
                print("⚡️ [MLX-VLM] Starting Speculative Decoding (MTP) Generation...", flush=True)
                generate_kwargs["draft_model"] = self.drafter
                generate_kwargs["draft_kind"] = self.draft_kind
                generate_kwargs["draft_block_size"] = 6
                generate_kwargs["temperature"] = 0.0
            else:
                generate_kwargs["temperature"] = 0.6

            response = stream_generate(**generate_kwargs)
            
            meter = TPSMeter()
            meter.start()
            
            import time
            last_chunk_time = time.time()

            for chunk in response:
                current_time = time.time()
                
                # MLX stream_generate는 Draft Hit 여부와 무관하게 청크를 1개씩 순차 반환합니다.
                # 연속된 토큰이 10ms(0.01초) 이하로 매우 빠르게 반환되면 Draft Hit으로 판별합니다.
                    
                meter.record_token()
                last_chunk_time = current_time

                # stream_generate가 반환하는 객체에서 텍스트 속성을 안전하게 추출
                yield chunk.text if hasattr(chunk, 'text') else chunk
                
            meter.stop("MLX")
            
        except Exception as e:
            log_error("Error in MLX chat generation", e)