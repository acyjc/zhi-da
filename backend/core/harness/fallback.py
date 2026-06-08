# FallbackHandler — 异常降级处理器，支持重试策略和元数据追踪
from .step import PipelineState


class FallbackHandler:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def handle(self, step_name: str, state: PipelineState, error: Exception) -> PipelineState:
        state.add_error(f"[Fallback] {step_name} 执行失败: {str(error)}")
        state.set(f"{step_name}_fallback", True)
        # Track fallback metadata for trace/reasoning propagation
        fb_count = state.metadata.get("fallback_count", 0) + 1
        state.metadata["fallback_count"] = fb_count
        state.metadata.setdefault("fallback_steps", []).append(step_name)
        state.metadata.setdefault("fallback_errors", {})[step_name] = str(error)
        return state
