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
        
        base_assistant_path = os.path.join("models", "mlx", "models--mlx-community--gemma-4-26B-A4B-it-assistant-bf16")
        print(f"🔍 [MLX-VLM] Checking drafter path: {os.path.abspath(base_assistant_path)}", flush=True)

        if os.path.exists(base_assistant_path) and "gemma-4" in model_name.lower():
            actual_assistant_path = base_assistant_path
            if not os.path.exists(os.path.join(actual_assistant_path, 'config.json')):
                for root, dirs, files in os.walk(base_assistant_path):
                    if 'config.json' in files:
                        actual_assistant_path = root
                        break

            try:
                from mlx_vlm.speculative.drafters import load_drafter
                self.draft_kind = "mtp"
                
                loaded_drafter = load_drafter(actual_assistant_path, kind=self.draft_kind)
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
            
            for chunk in response:
                meter.record_token()

                yield chunk.text if hasattr(chunk, 'text') else chunk
                
            meter.stop("MLX")
            
        except Exception as e:
            log_error("Error in MLX chat generation", e)