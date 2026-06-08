# PipelineRunner 状态驱动执行器——按序执行 PipelineStep 列表，支持进度回调、RunLogger 和异常降级
import logging
import time
from typing import Callable
from .step import PipelineStep, PipelineState
from .logger import RunLogger

logger = logging.getLogger(__name__)


# Pipeline 运行引擎
class PipelineRunner:
    def __init__(self, steps: list[PipelineStep], fallback_handler: Callable = None):
        self.steps = steps
        self.fallback_handler = fallback_handler
        self.run_logger = RunLogger()

    async def run(self, state: PipelineState, on_progress: Callable = None) -> PipelineState:
        state.metadata["pipeline_start"] = time.time()
        total = len(self.steps)
        for i, step in enumerate(self.steps):
            step_start = time.time()
            error_msg = ""
            try:
                if on_progress:
                    await on_progress(step.name, (i + 1) / total, f"正在执行: {step.name}")
                state = await step.execute(state)
                duration_ms = (time.time() - step_start) * 1000
                state.metadata[f"{step.name}_duration"] = duration_ms
                self.run_logger.log(
                    step_name=step.name,
                    input_summary=str(state.input.get(step.name, ""))[:200],
                    output_summary=str(state.results.get(step.name, ""))[:200],
                    duration_ms=round(duration_ms, 2),
                )
            except Exception as e:
                duration_ms = (time.time() - step_start) * 1000
                error_msg = str(e)
                logger.error(f"Pipeline step '{step.name}' failed: {e}", exc_info=True)
                state.add_error(f"{step.name}: {str(e)}")
                self.run_logger.log(
                    step_name=step.name,
                    duration_ms=round(duration_ms, 2),
                    error=error_msg,
                )
                if self.fallback_handler:
                    await self.fallback_handler(step.name, state, e)
                else:
                    break
            if state.has_errors() and not self.fallback_handler:
                break
        state.metadata["pipeline_duration"] = time.time() - state.metadata["pipeline_start"]
        # Write RunLogger summary into metadata for downstream trace/reasoning
        state.metadata["run_log"] = self.run_logger.to_dict()
        state.metadata["run_log_summary"] = self.run_logger.summary()
        return state

    def get_run_logger(self) -> RunLogger:
        return self.run_logger
