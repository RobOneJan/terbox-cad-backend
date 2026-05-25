import json
from pathlib import Path
from typing import List

_REGISTRY: dict = json.loads((Path(__file__).parent / "component_registry.json").read_text(encoding="utf-8"))

# How much of the tube length each connector arm occupies (mm)
_ARM_MM = 120


def _part(key: str, qty: int, **extra) -> dict:
    comp = _REGISTRY.get(key, {})
    item = {
        "component_key": key,
        "article_nr": comp.get("article_nr", "TBD"),
        "description": comp.get("description", key),
        "qty": qty,
    }
    item.update({k: v for k, v in extra.items() if v is not None})
    return item


def bom_for_box(
    length_mm: float,
    width_mm: float,
    height_mm: float,
    with_roof: bool = True,
    with_floor: bool = True,
) -> List[dict]:
    """BOM for a rectangular box using AB1000 connectors and 100x100 tubes."""
    inner_l = round(length_mm - 2 * _ARM_MM)
    inner_w = round(width_mm  - 2 * _ARM_MM)
    inner_h = round(height_mm - 2 * _ARM_MM)
    o = _ARM_MM - 75  # = 45mm, tube center offset in perpendicular plane
    needs_front_post = (length_mm - 2 * o) > 2500.0

    parts = [
        _part("y_corner",        qty=8),
        _part("tube_100x100",    qty=4, length_mm=inner_l, note=f"Längsträger {inner_l} mm"),
        _part("tube_100x100",    qty=4, length_mm=inner_w, note=f"Querträger {inner_w} mm"),
        _part("tube_100x100",    qty=4, length_mm=inner_h, note=f"Stützen {inner_h} mm"),
        _part("bolt_m12_120_a2", qty=72),  # 3 bolts/arm x 3 arms x 8 corners
        _part("nut_m12",         qty=72),
    ]

    if with_roof:
        parts += [
            _part("roof_substructure", qty=2),
            _part("roof_panel",        qty=2),
        ]

    if needs_front_post:
        parts.append(_part("tube_100x100", qty=1, length_mm=inner_h, note="Mittelpost Vorne"))
        if not with_floor:
            parts.append(_part("base_plate", qty=1, note="Fußstück Mittelpost Vorne"))

    return parts
