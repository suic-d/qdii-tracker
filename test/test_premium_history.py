"""历史溢价对齐计算的纯逻辑单测。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pipeline.premium_history import align_premium


def test_align_premium_basic():
    closes = [{"date": "2026-09-01", "close": 1.10}, {"date": "2026-09-02", "close": 1.05}]
    navs = [{"date": "2026-09-01", "nav": 1.00}, {"date": "2026-09-02", "nav": 1.00}]
    out = align_premium(closes, navs)
    assert [r["premium"] for r in out] == [10.0, 5.0]


def test_align_premium_skips_missing_nav():
    closes = [{"date": "2026-09-01", "close": 1.10}, {"date": "2026-09-02", "close": 1.05}]
    navs = [{"date": "2026-09-01", "nav": 1.00}]
    out = align_premium(closes, navs)
    assert len(out) == 1


def test_align_premium_skips_zero_nav():
    closes = [{"date": "2026-09-01", "close": 1.10}]
    navs = [{"date": "2026-09-01", "nav": 0}]
    assert align_premium(closes, navs) == []
