"""sparkline 数据裁剪的纯逻辑单测。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pipeline.sparklines import trim_series


def test_trim_series_empty():
    assert trim_series([]) == []
    assert trim_series(None) == []


def test_trim_series_keeps_last_n():
    pts = list(range(100))
    assert trim_series(pts, 30) == list(range(70, 100))


def test_trim_series_shorter_than_n():
    pts = [1, 2, 3]
    assert trim_series(pts, 30) == pts
