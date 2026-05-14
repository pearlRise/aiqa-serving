#============================================================
# - subject: mlx_manager.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Apple MLX framework based LLM model controller and text stream manager.
# - caution: Ensure proper memory management when loading/unloading models.
#============================================================
import os
from tool.exception_logging import log_error

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
        potential_drafter = model_name.replace("it-bf16", "it-assistant-bf16").replace("it", "it-assistant")
        assistant_path = os.path.join("models", "mlx", potential_drafter)
        
        # 특정 모델명에 대한 Fallback 경로 탐색
        if not os.path.exists(assistant_path):
            fallback = os.path.join("models", "mlx", "gemma-4-26B-A4B-it-assistant-bf16")
            if os.path.exists(fallback) and "gemma-4" in model_name.lower():
                assistant_path = fallback

        if os.path.exists(assistant_path):
            try:
                from mlx_vlm.speculative.drafters import load_drafter
                self.draft_kind = "mtp" if "gemma-4" in model_name.lower() else "dflash"
                
                self.drafter = load_drafter(assistant_path, kind=self.draft_kind)
                mx.eval(self.drafter)
                print(f"🚀 [MLX-VLM] Drafter ({self.draft_kind}) loaded from {assistant_path}")
            except Exception as e:
                log_error("Failed to load drafter model", e)

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
                model=self.model, 
                processor=self.processor, 
                prompt=prompt,
                max_tokens=1024
            }

            if self.drafter:
                generate_kwargs["draft_model"] = self.drafter
                generate_kwargs["draft_kind"] = self.draft_kind
                generate_kwargs["draft_block_size"] = 6
                generate_kwargs["temperature"] = 0.0
            else:
                generate_kwargs["temperature"] = 0.6

            response = stream_generate(**generate_kwargs)
            
            for chunk in response:
                # stream_generate가 반환하는 객체에서 텍스트 속성을 안전하게 추출
                yield chunk.text if hasattr(chunk, 'text') else chunk
            
        except Exception as e:
            log_error("Error in MLX chat generation", e)