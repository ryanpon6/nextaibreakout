"""npm/PyPI 7-day multiplier must vanish when any window day is zero or missing."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from score import window_ok
import seo2
def it(days, m=500, src="npm"):
    return {"id": "npm:x", "source": src, "metric": m, "metric_name": "downloads/day", "extra": {"week": sum(days or [0]), "days": days}}
def test_normal(): x = it([100,110,90,120,100,130,500]); assert window_ok(x) and "× 7-day avg" in seo2.measure(x)
def test_zero(): x = it([0,0,0,872,0,0,0]); assert not window_ok(x) and "×" not in seo2.measure(x)
def test_one_zero(): assert not window_ok(it([100,110,0,120,100,130,500]))
def test_missing(): x = it([100,110,120,500]); assert not window_ok(x) and "×" not in seo2.measure(x)
def test_no_days(): x = it(None); assert not window_ok(x)
if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"): f(); print("ok", k)
