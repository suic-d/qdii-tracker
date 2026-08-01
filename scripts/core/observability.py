"""
scripts/core/observability.py — 轻量操作日志

不引入第三方库。记录 pipeline 每一步的操作、时间戳、结果。
"""
import json
import time
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent.parent / ".loop"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "run_log.jsonl"


def log_step(step: str, category: str = "", result: str = "ok", detail: str = ""):
    """追加一行 JSON 日志到 run_log.jsonl"""
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "step": step,
        "category": category,
        "result": result,
        "detail": detail,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_sync_start():
    log_step("sync", result="start")


def log_sync_done(files: list):
    log_step("sync", result="ok", detail=f"updated: {','.join(files)}" if files else "no changes")


def log_check_pass(layers_passed: int):
    log_step("check", result="ok", detail=f"layers: {layers_passed}")


def log_check_fail(layer: int, reason: str):
    log_step("check", result="fail", detail=f"layer {layer}: {reason}")
