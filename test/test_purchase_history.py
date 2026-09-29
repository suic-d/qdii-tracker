"""申购历史边界逻辑的回归测试（fill.py 的纯函数部分）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pipeline.fill import _normalize_purchase_state, _compact_history, _update_history


def _rmb(code="016055"):
    return {"code": code, "currency": "人民币", "buy_status": "暂停申购", "daily_limit": 100.0}


def test_normalize_paused_share_limit_to_none():
    sh = _rmb()
    _normalize_purchase_state(sh)
    assert sh["daily_limit"] is None


def test_normalize_historical_paused_limit_regardless_of_current_status():
    sh = {
        "code": "008763",
        "currency": "人民币",
        "buy_status": "限大额",
        "daily_limit": 1000.0,
        "buy_status_history": [
            {"date": "2026-08-29", "buy_status": "暂停申购", "daily_limit": 100.0},
            {"date": "2026-09-03", "buy_status": "限大额", "daily_limit": 500.0},
        ],
    }
    _normalize_purchase_state(sh)
    assert sh["daily_limit"] == 1000.0  # 当前限大额不被归一
    assert sh["buy_status_history"][0]["daily_limit"] is None  # 历史暂停额度归一
    assert sh["buy_status_history"][1]["daily_limit"] == 500.0


def test_compact_removes_consecutive_duplicates():
    sh = {
        "buy_status_history": [
            {"date": "2026-08-29", "buy_status": "暂停申购", "daily_limit": None},
            {"date": "2026-09-02", "buy_status": "暂停申购", "daily_limit": None},
            {"date": "2026-09-03", "buy_status": "限大额", "daily_limit": 500.0},
        ]
    }
    _compact_history(sh)
    assert [h["date"] for h in sh["buy_status_history"]] == ["2026-08-29", "2026-09-03"]


def test_compact_keeps_limit_changes():
    sh = {
        "buy_status_history": [
            {"date": "2026-09-03", "buy_status": "限大额", "daily_limit": 500.0},
            {"date": "2026-09-19", "buy_status": "限大额", "daily_limit": 1000.0},
        ]
    }
    _compact_history(sh)
    assert len(sh["buy_status_history"]) == 2


def test_update_history_does_not_append_paused_limit_noise():
    sh = _rmb()
    sh["buy_status_history"] = [
        {"date": "2026-07-11", "buy_status": "暂停申购", "daily_limit": 100.0}
    ]
    # 暂停态 daily_limit 从 100 变为 None，仅是噪音，不应追加新条目
    sh["daily_limit"] = None
    _update_history(sh, "2026-09-08")
    assert len(sh["buy_status_history"]) == 1


def test_update_history_appends_limit_change_when_limited():
    sh = {
        "code": "008763",
        "currency": "人民币",
        "buy_status": "限大额",
        "daily_limit": 1000.0,
        "buy_status_history": [
            {"date": "2026-09-03", "buy_status": "限大额", "daily_limit": 500.0}
        ],
    }
    _update_history(sh, "2026-09-19")
    assert len(sh["buy_status_history"]) == 2
    assert sh["buy_status_history"][-1]["daily_limit"] == 1000.0


def test_update_history_skips_etf_and_usd():
    for sh in (
        {"code": "513500", "currency": "人民币", "buy_status": "暂停申购", "daily_limit": None},
        {"code": "016055", "currency": "美元", "buy_status": "暂停申购", "daily_limit": None},
    ):
        _update_history(sh, "2026-09-08")
        assert "buy_status_history" not in sh
