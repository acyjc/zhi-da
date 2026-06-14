# RunLogger — 运行日志记录器，记录每步耗时、Token 用量、错误信息
import time
from dataclasses import dataclass, field


@dataclass
class RunRecord:
    step_name: str = ""
    input_summary: str = ""
    output_summary: str = ""
    duration_ms: float = 0
    token_usage: dict = field(default_factory=dict)
    error: str = ""
    timestamp: float = field(default_factory=time.time)


class RunLogger:
    def __init__(self):
        self.records: list[RunRecord] = []

    def log(self, step_name: str, input_summary: str = "", output_summary: str = "",
            duration_ms: float = 0, token_usage: dict = None, error: str = ""):
        record = RunRecord(
            step_name=step_name, input_summary=input_summary, output_summary=output_summary,
            duration_ms=duration_ms, token_usage=token_usage or {}, error=error,
        )
        self.records.append(record)

    def to_dict(self) -> list[dict]:
        return [r.__dict__ for r in self.records]

    def summary(self) -> dict:
        total_duration = sum(r.duration_ms for r in self.records)
        total_tokens = sum(r.token_usage.get("total_tokens", 0) for r in self.records)
        errors = [r for r in self.records if r.error]
        return {
            "total_steps": len(self.records),
            "total_duration_ms": total_duration,
            "total_tokens": total_tokens,
            "error_count": len(errors),
            "errors": [{"step": r.step_name, "error": r.error} for r in errors],
        }
