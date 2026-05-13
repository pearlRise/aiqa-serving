import os

class MlxManager:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.active_model = None

    def load_model(self, model_name):
        try:
            import mlx_lm
        except ImportError:
            raise ImportError("mlx-lm 라이브러리가 설치되지 않았습니다. 터미널에서 'pip install mlx-lm'을 실행해 주세요.")

        model_path = os.path.join("models", "mlx", model_name)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"모델 경로를 찾을 수 없습니다: {model_path}")

        self.model, self.tokenizer = mlx_lm.load(model_path)
        self.active_model = model_name
        return True

    def unload_model(self):
        self.model = None
        self.tokenizer = None
        self.active_model = None
        return True

    def chat_stream(self, prompt):
        try:
            from mlx_lm import stream_generate
            
            # stream_generate는 제너레이터로서 응답을 청크 단위로 반환합니다.
            response = stream_generate(self.model, self.tokenizer, prompt=prompt, max_tokens=1024)
            for chunk in response:
                yield chunk.text if hasattr(chunk, 'text') else str(chunk)
        except Exception as e:
            yield f"\n[생성 실패: {str(e)}]"