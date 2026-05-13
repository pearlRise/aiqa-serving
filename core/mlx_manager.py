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
        except ImportError:
            raise ImportError("mlx-lm 라이브러리가 설치되지 않았습니다. 터미널에서 'pip install mlx-lm'을 실행해 주세요.")

        base_model_path = os.path.join("models", "mlx", model_name)
        if not os.path.isdir(base_model_path):
            raise FileNotFoundError(f"모델 디렉터리를 찾을 수 없습니다: {base_model_path}")

        # config.json 파일의 실제 위치를 탐색
        actual_model_path = base_model_path
        if not os.path.exists(os.path.join(actual_model_path, 'config.json')):
            # 하위 디렉터리에서 config.json 탐색 (e.g. snapshots/...)
            found = False
            for root, dirs, files in os.walk(base_model_path):
                if 'config.json' in files:
                    actual_model_path = root
                    print(f"Found config.json in a subdirectory: {actual_model_path}")
                    found = True
                    break
            if not found:
                raise FileNotFoundError(f"'config.json'을 {base_model_path} 또는 그 하위 디렉터리에서 찾을 수 없습니다.")
        
        print(f"Loading model from: {actual_model_path}")
        self.model, self.tokenizer = mlx_lm.load(actual_model_path)
        # 모델의 모든 파라미터와 버퍼를 평가하여 현재 쓰레드의 스트림에 완전히 로드합니다.
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

            # 다른 쓰레드에서 로드된 모델을 현재 쓰레드에서 사용하기 위해 모델 전체를 다시 평가합니다.
            mx.eval(self.model)
            
            # stream_generate는 제너레이터로서 응답을 청크 단위로 반환합니다.
            response = stream_generate(self.model, self.tokenizer, prompt=prompt, max_tokens=1024)
            for chunk in response:
                yield chunk.text if hasattr(chunk, 'text') else str(chunk)
        except Exception as e:
            yield f"[생성 실패: {str(e)}]"