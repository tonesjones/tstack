"""Behavior check: exits non-zero if inventory.py behaves differently from the spec."""
import json, sys, tempfile, os
sys.path.insert(0, os.getcwd())
import inventory as inv

stock = {"a": 2, "b": 10, "c": 0}
assert inv.low_stock(stock) == ["a", "c"]
assert inv.total_units(stock) == 12
assert inv.restock_plan(stock, {"a": 5, "b": 10, "c": 600, "d": 3}) == {"a": 3, "c": 500, "d": 3}
assert inv.restock_plan(stock, {}) == {}
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "t.json")
    open(p, "w").write('{"a": 4}')
    assert inv.load_targets(p) == {"a": 4}
    open(p, "w").write("{nope")
    try:
        inv.load_targets(p)
    except ValueError:
        pass
    else:
        raise SystemExit("load_targets must raise ValueError on bad JSON")
print("behavior ok")
