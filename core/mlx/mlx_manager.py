#============================================================
# - subject: mlx_manager.py
# - created: 2026-05-13
# - updated: 2026-05-14
# - summary: Loads Apple MLX models and handles text streams.
# - caution: Requires mlx_lm library and valid model paths.
#============================================================
import os
from tool.exception_logging import log_error
from tool.evaluation_tps import TPSMeter

# Apple MLX 프레임워크 기반 LLM 모델 제어 및 텍스트 추론 전담 매니저
class MlxManager:
    # MLX 모델, 토크나이저 및 상태 변수 초기화
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.active_model = None
        self.drafter = None

    # MLX 라이브러리를 동적 로드하고 모델 경로를 검증하여 메모리에 적재
    def load_model(self, model_name):
        try:
            # 1. 무거운 MLX 모듈 동적 임포트로 앱 초기 구동 속도 개선
            import mlx.core as mx
            import mlx_lm
        except ImportError as e:
            log_error("Failed to import MLX modules", e)
            raise

        base_model_path = os.path.join("models", "mlx", model_name)
        if not os.path.isdir(base_model_path):
            log_error("Model directory not found", Exception(base_model_path))
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
                log_error("config.json not found in model path")
                raise FileNotFoundError("config.json not found")
        
        # 3. 모델과 토크나이저 로드 후 eval 모드로 전환하여 GPU 점유 최적화
        self.model, self.tokenizer = mlx_lm.load(actual_model_path)
        mx.eval(self.model)
        self.active_model = model_name
        
        # 4. MTP(Multi-Token Prediction) 드래프터 모델 로드 시도
        # 다운로드하신 폴더 이름이 정확히 일치해야 합니다. (models/mlx/gemma-4-26B-A4B-it-assistant-bf16)
        assistant_path = os.path.join("models", "mlx", "gemma-4-26B-A4B-it-assistant-bf16")
        # 주의: 호환성을 위해 메인 모델 이름에 'gemma'가 포함되어 있을 때만 드래프터를 로드하도록 조건 추가
        if "gemma" in model_name.lower() and os.path.exists(assistant_path):
            try:
                # 4.1 드래프터 모델 역시 config.json이 위치한 실제 하위 폴더 탐색
                actual_assistant_path = assistant_path
                if not os.path.exists(os.path.join(actual_assistant_path, 'config.json')):
                    for root, dirs, files in os.walk(assistant_path):
                        if 'config.json' in files:
                            actual_assistant_path = root
                            break
                            
                from mlx_lm.utils import load_drafter
                self.drafter = load_drafter(actual_assistant_path, kind="mtp")
                mx.eval(self.drafter)
                print(f"[MLX] 🚀 MTP Drafter successfully loaded from {actual_assistant_path}")
            except Exception as e:
                log_error("Failed to load drafter model", e)
        if self.drafter:
        # 드래프터 모델의 첫 번째 레이어 파라미터가 존재하는지 확인
            print(f"🔍 [DEBUG] Drafter weights loaded: {len(self.drafter.parameters()) > 0}")
        return True

    # GPU 메모리 확보를 위해 현재 로드된 모델과 토크나이저 할당 해제
    def unload_model(self):
        self.model = None
        self.tokenizer = None
        self.active_model = None
        self.drafter = None
        return True

    # MLX_LM의 stream_generate를 사용하여 프롬프트 추론 청크 yield
    def chat_stream(self, prompt):
        try:
            import mlx.core as mx
            from mlx_lm import stream_generate
            from mlx_lm.sample_utils import make_sampler, make_logits_processors

            mx.eval(self.model)
            
            # 1. 모델이 대화 문맥을 올바르게 이해하도록 Chat Template 적용
            if hasattr(self.tokenizer, "apply_chat_template") and self.tokenizer.chat_template:
                messages = [{"role": "user", "content": prompt}]
                prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

            # 2. 같은 단어의 무의미한 반복을 억제하는 패널티(1.1 ~ 1.2 사이 권장) 추가
            sampler = make_sampler(temp=0.7)
            logits_processors = make_logits_processors(repetition_penalty=1.15)

            generate_kwargs = {
                "max_tokens": 1024,
                "sampler": sampler,
                "logits_processors": logits_processors
            }
            
            if self.drafter:
                # MTP 드래프터 전용 필수 파라미터 적용
                generate_kwargs["draft_model"] = self.drafter
                generate_kwargs["draft_kind"] = "mtp"
                generate_kwargs["draft_block_size"] = 6
                # MTP는 logits processor와 충돌 시 무한 대기(Hang)를 유발하므로 제거하고 가장 안정적인 temp=0.0으로 덮어씌웁니다.
                generate_kwargs["sampler"] = make_sampler(temp=0.0)
                if "logits_processors" in generate_kwargs:
                    del generate_kwargs["logits_processors"]

            # 최대 토큰 제한(1024)을 적용하여 텍스트 스트리밍 생성
            response = stream_generate(self.model, self.tokenizer, prompt=prompt, **generate_kwargs)
            
            meter = TPSMeter()
            meter.start()
            for chunk in response:
                token_count = 0
                text_to_yield = ""

                if hasattr(chunk, 'text') and hasattr(chunk, 'tokens'):
                    token_count = len(chunk.tokens)
                    text_to_yield = chunk.text
                    if token_count > 1:
                        print(f"🎯 [Draft Hit] {token_count} tokens accepted!")
                elif isinstance(chunk, str):
                    token_count = 1 if chunk else 0
                    text_to_yield = chunk

                if token_count > 0:
                    meter.record_token(token_count)

                if text_to_yield:
                    yield text_to_yield
            meter.stop("MLX")
        except Exception as e:
            # 추론 중 메모리 부족 또는 모델 이상 발생 시 예외 처리
            log_error("Error in MLX chat generation", e)
