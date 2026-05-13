import os

class MlxManager:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.active_model = None

    def load_model(self, model_name):
        try:
            import mlx.core as mx
            import mlx_lm
        except ImportError as e:
            print(f"ImportError: {e}")
            raise

        base_model_path = os.path.join("models", "mlx", model_name)
        if not os.path.isdir(base_model_path):
            print(f"FileNotFoundError: {base_model_path}")
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
                print(f"FileNotFoundError: config.json not found in {base_model_path}")
                raise FileNotFoundError("config.json not found")
        
        self.model, self.tokenizer = mlx_lm.load(actual_model_path)
        mx.eval(self.model)
        self.active_model = model_name
        return True

    def unload_model(self):
        self.model = None
        self.tokenizer = None
        self.active_model = None
        return True

    def chat_stream(self, prompt):
        try:
            import mlx.core as mx
            from mlx_lm import stream_generate

            mx.eval(self.model)
            
            response = stream_generate(self.model, self.tokenizer, prompt=prompt, max_tokens=1024)
            for chunk in response:
                yield chunk.text if hasattr(chunk, 'text') else str(chunk)
        except Exception as e:
            print(f"MlxManager Chat Stream Error: {e}")