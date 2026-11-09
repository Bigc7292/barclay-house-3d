"""Fallback classifier: Python port of the keyword + image-signal rules in
offplan-reconstruct src/lib/classify.ts (localClassify), reduced to the 4 coarse classes.
Used with --classifier local, or automatically when open_clip/torch are not installed."""
import re

LEVEL = re.compile(r"\b(basement|ground\s*floor|first\s*floor|second\s*floor|third\s*floor|mezzanine|podium|roof\s*top|rooftop|roof|typical\s*floor|level\s*\d+|penthouse|upper\s*floor|lower\s*floor)\b", re.I)
ROOM = re.compile(r"\b(bed\s*room|bedroom|master|guest|kitchen|living|lounge|dining|majlis|maid|driver|laundry|powder|bath(room)?|toilet|wc|en-?suite|balcony|terrace|pool|store|storage|lift|lobby|entrance|foyer|family|dress(ing)?|walk-?in|wardrobe|closet|study|office|gym|cinema|garage|parking|pantry|utility|garden|deck)\b", re.I)
DIM = re.compile(r"\b\d{1,2}[.,]\d{1,2}\s*m?\s*[x×X]\s*\d{1,2}[.,]\d{1,2}|\b\d{4}\s*[x×X]\s*\d{4}\b")
INTERIOR = re.compile(r"\b(bed\s*room|bedroom|living|lounge|dining|kitchen|bath|powder|entrance|foyer|majlis|office|gym|cinema|closet|walk-?in|dressing|interior)\b", re.I)
EXTERIOR = re.compile(r"\b(exterior|facade|façade|aerial|elevation view|street|night view|pool view|garden view|front view|rear view)\b", re.I)


def classify(text: str, st: dict) -> tuple[str, dict]:
    """st = page image stats: white_ratio, saturation, color_std, edge_density (0..1, 0..1, 0..255, 0..1)."""
    s = {"floor_plan": 0.0, "exterior": 0.0, "interior": 0.0, "other": 0.0}
    levels, rooms, dims = len(LEVEL.findall(text)), len(ROOM.findall(text)), len(DIM.findall(text))
    if re.search(r"floor\s*plan|unit\s*plan|layout|key\s*plan|typical\s*floor", text, re.I): s["floor_plan"] += 1.5
    if levels >= 1 and rooms >= 4: s["floor_plan"] += 1 + min(2, rooms / 6)
    if dims >= 2: s["floor_plan"] += 1.5
    if re.search(r"\belevation\b", text, re.I) and not re.search(r"elevator", text, re.I): s["exterior"] += 1.5
    if re.search(r"renders?\b|cgi|visuali[sz]ation", text, re.I):
        s["interior" if re.search("interior", text, re.I) else "exterior" if re.search("exterior", text, re.I) else "interior"] += 1.2
    photo = st["color_std"] > 45 and st["saturation"] > 0.12 and st["white_ratio"] < 0.35
    drawing = st["white_ratio"] > 0.25 and st["saturation"] < 0.12 and st["edge_density"] > 0.04
    if photo: s["exterior" if EXTERIOR.search(text) or not rooms else "interior"] += 1.4
    if drawing and rooms >= 2: s["floor_plan"] += 1
    if INTERIOR.search(text) and photo: s["interior"] += 0.5
    best = max(s, key=s.get)
    return (best if s[best] >= 1.4 else "other"), s
