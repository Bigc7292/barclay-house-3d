"""Fast checks for the parts that need no models: dimension parsing, wrapped labels, room pairing, empty-page rule.
  python tools/brochure_triage/eval/selftest.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from triage import room_dims, empty_page, DIM  # noqa: E402

assert [m.group(0) for m in DIM.finditer("SWIMMING POOL 9.50m x 2.40m")] == ["9.50m x 2.40m"]
assert DIM.search("WC 1500x2972") and DIM.search("4.00×6.00") and not DIM.search("263.01 Sq.m")
items = [("LIVING", [100, 100, 160, 115], 0.99), ("5.95 X", [100, 118, 150, 132], 0.98), ("4.97", [105, 134, 140, 148], 0.97),
         ("BEDROOM 1", [400, 100, 480, 115], 0.99), ("4225x5135", [402, 118, 470, 132], 0.95)]
d = room_dims(items, 1000, 1000)
assert [(x["room_guess"], x["dims"]) for x in d] == [("LIVING", "5.95 × 4.97"), ("BEDROOM 1", "4225 × 5135")], d
flat = {"white_ratio": 0.0, "gray_std": 5.0}
assert empty_page("5 BEDROOM VILLA", flat) and not empty_page("x" * 200, flat)
print("selftest OK")
