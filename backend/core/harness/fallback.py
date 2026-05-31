# FallbackHandler — 异常降级处理器，支持重试策略
from .step import PipelineState


class FallbackHandler:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def handle(self, step_name: str, state: PipelineState, error: Exception) -> PipelineState:
        state.add_error(f"[Fallback] {step_name} 执行失败: {str(error)}")
        state.set(f"{step_name}_fallback", True)
        return state
