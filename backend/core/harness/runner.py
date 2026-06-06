# PipelineRunner 状态驱动执行器——按序执行 PipelineStep 列表，支持进度回调和异常降级
import logging
import time
from typing import Callable
from .step import PipelineStep, PipelineState

logger = logging.getLogger(__name__)


# Pipeline 运行引擎
class PipelineRunner:
    def __init__(self, steps: list[PipelineStep], fallback_handler: Callable = None):
        self.steps = steps
        self.fallback_handler = fallback_handler

    async def run(self, state: PipelineState, on_progress: Callable = None) -> PipelineState:
        state.metadata["pipeline_start"] = time.time()
        total = len(self.steps)
        for i, step in enumerate(self.steps):
            step_start = time.time()
            try:
                if on_progress:
                    await on_progress(step.name, (i + 1) / total, f"正在执行: {step.name}")
                state = await step.execute(state)
                state.metadata[f"{step.name}_duration"] = time.time() - step_start
            except Exception as e:
                logger.error(f"Pipeline step '{step.name}' failed: {e}", exc_info=True)
                state.add_error(f"{step.name}: {str(e)}")
                if self.fallback_handler:
                    await self.fallback_handler(step.name, state, e)
                else:
                    break
            if state.has_errors() and not self.fallback_handler:
                break
        state.metadata["pipeline_duration"] = time.time() - state.metadata["pipeline_start"]
        return state
