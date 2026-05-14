#============================================================
# - subject: mlx_manager.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Loads Apple MLX models and handles text streams.
# - caution: Requires mlx_lm library and valid model paths.
#============================================================
import os

# Apple MLX 프레임워크 기반 LLM 모델 제어 및 텍스트 추론 전담 매니저
class MlxManager:
    # MLX 모델, 토크나이저 및 상태 변수 초기화
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.active_model = None

    # MLX 라이브러리를 동적 로드하고 모델 경로를 검증하여 메모리에 적재
    def load_model(self, model_name):
        try:
            # 1. 무거운 MLX 모듈 동적 임포트로 앱 초기 구동 속도 개선
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
            # 2. 하위 디렉토리를 탐색하여 config.json이 위치한 실제 모델 폴더 찾기
            found = False
            for root, dirs, files in os.walk(base_model_path):
                if 'config.json' in files:
                    actual_model_path = root
                    found = True
                    break
            if not found:
                print(f"FileNotFoundError: config.json not found in {base_model_path}")
                raise FileNotFoundError("config.json not found")
        
        # 3. 모델과 토크나이저 로드 후 eval 모드로 전환하여 GPU 점유 최적화
        self.model, self.tokenizer = mlx_lm.load(actual_model_path)
        mx.eval(self.model)
        self.active_model = model_name
        return True

    # GPU 메모리 확보를 위해 현재 로드된 모델과 토크나이저 할당 해제
    def unload_model(self):
        self.model = None
        self.tokenizer = None
        self.active_model = None
        return True

    # MLX_LM의 stream_generate를 사용하여 프롬프트 추론 청크 yield
    def chat_stream(self, prompt):
        try:
            import mlx.core as mx
            from mlx_lm import stream_generate

            mx.eval(self.model)
            
            # 최대 토큰 제한(1024)을 적용하여 텍스트 스트리밍 생성
            response = stream_generate(self.model, self.tokenizer, prompt=prompt, max_tokens=1024)
            for chunk in response:
                yield chunk.text if hasattr(chunk, 'text') else str(chunk)
        except Exception as e:
            # 추론 중 메모리 부족 또는 모델 이상 발생 시 예외 처리
            print(f"MlxManager Chat Stream Error: {e}")