#============================================================
# - subject: evaluation_tps.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Utility for measuring Tokens Per Second (TPS).
# - caution: None.
#============================================================
import time
from tool.exception_logging import log_info

class TPSMeter:
    def __init__(self):
        self.start_time = None
        self.first_token_time = None
        self.token_count = 0
        # 성능 측정 기능 활성화 상태
        self.is_active = True

    def start(self):
        if not self.is_active: return
        self.start_time = time.time()
        self.first_token_time = None
        self.token_count = 0

    def record_token(self, count=1):
        if not self.is_active: return
        if self.first_token_time is None:
            self.first_token_time = time.time()
        self.token_count += count

    def stop(self, engine_name="Engine"):
        if not self.is_active or not self.start_time or not self.first_token_time:
            return
        
        ttft = self.first_token_time - self.start_time
        gen_time = time.time() - self.first_token_time
        
        tps = (self.token_count - 1) / gen_time if self.token_count > 1 and gen_time > 0 else 0.0
            
        log_info(f"[{engine_name} Performance] TTFT: {ttft:.3f}s | TPS: {tps:.2f} tokens/sec | Total: {self.token_count} tokens")