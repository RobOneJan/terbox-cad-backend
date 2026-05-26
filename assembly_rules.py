import json
from pathlib import Path
from typing import List

_REGISTRY: dict = json.loads((Path(__file__).parent / "component_registry.json").read_text(encoding="utf-8"))

_ARM_MM = 120  # arm length of every connector


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
    walls: str = "full",           # "full" | "half" | "none"
    wall_material: str | None = None,
    floor_material: str | None = None,
    roller_door: bool = False,
) -> List[dict]:
    """BOM for a rectangular box using AB1000 connectors and 100×100 tubes."""
    a = _ARM_MM
    o = a - 75  # = 45 mm — tube cross-section center offset from junction center

    L, W, H = length_mm, width_mm, height_mm
    _needs_mid_post  = (L - 2 * o) > 2500.0
    _needs_side_post = (W - 2 * o) > 2500.0

    inner_l = round(L - 2 * a)
    inner_w = round(W - 2 * a)
    inner_h = round(H - 2 * a)

    # ── Connectors ───────────────────────────────────────────────────────────
    # Without floor: front-bottom two Y-Ecke become L-Ecke (no X arm)
    n_y = 8 if with_floor else 6
    n_l = 0 if with_floor else 2
    n_t = 2 if _needs_mid_post else 0  # T-Ecke at top of front + back mid-post

    parts: List[dict] = []
    parts.append(_part("y_corner", qty=n_y))
    if n_l:
        parts.append(_part("l_corner", qty=n_l))
    if n_t:
        parts.append(_part("t_corner", qty=n_t))

    # ── Tubes ─────────────────────────────────────────────────────────────────
    # X (length) — 4 positions: front-bottom, back-bottom, front-top, back-top
    #   front-bottom omitted when no floor
    #   front-top + back-top replaced by 4 split halves when mid-post present
    n_x_omit = (1 if not with_floor else 0) + (2 if _needs_mid_post else 0)
    n_x_full = 4 - n_x_omit
    if n_x_full > 0:
        parts.append(_part("tube_100x100", qty=n_x_full, length_mm=inner_l,
                           note=f"Längsträger {inner_l} mm"))
    if _needs_mid_post:
        half_len = round(L / 2 - 3 * a)
        parts.append(_part("tube_100x100", qty=4, length_mm=half_len,
                           note=f"Längsträger oben geteilt {half_len} mm"))

    # Y (depth)
    parts.append(_part("tube_100x100", qty=4, length_mm=inner_w,
                       note=f"Querträger {inner_w} mm"))

    # Z (height) — corner posts
    parts.append(_part("tube_100x100", qty=4, length_mm=inner_h,
                       note=f"Stützen {inner_h} mm"))

    # Middle posts (front + back) when span > 2500 mm
    if _needs_mid_post:
        parts.append(_part("tube_100x100", qty=2, length_mm=inner_h,
                           note=f"Mittelpost {inner_h} mm"))
        if not with_floor:
            parts.append(_part("base_plate", qty=1, note="Fußstück Mittelpost Vorne"))

    # ── Hardware ──────────────────────────────────────────────────────────────
    # 3 bolts per arm-tube junction; Y-Ecke has 3 arms, L-Ecke 2, T-Ecke 3
    n_junctions = n_y * 3 + n_l * 2 + n_t * 3
    n_bolts = n_junctions * 3
    parts.append(_part("bolt_m12_120_a2", qty=n_bolts))
    parts.append(_part("nut_m12",         qty=n_bolts))

    # ── Roof ──────────────────────────────────────────────────────────────────
    if with_roof:
        dim = f"{round(L - 2*o)}×{round(W - 2*o)} mm"
        parts.append(_part("roof_substructure", qty=1, note=dim))
        parts.append(_part("roof_panel",        qty=1, note=dim))

    # ── Floor panel ───────────────────────────────────────────────────────────
    if with_floor:
        mat = floor_material or "TBD"
        parts.append(_part("floor_panel", qty=1,
                           note=f"{round(L-2*o)}×{round(W-2*o)} mm, {mat}"))

    # ── Walls + Schienen ──────────────────────────────────────────────────────
    if walls != "none":
        panel_h   = round((H - 2 * o) / 2 if walls == "half" else H - 2 * o)
        span_l    = round(L - 2 * o)
        span_w    = round(W - 2 * o)
        pw        = 100  # middle-post tube width
        mat_label = wall_material or "TBD"

        # Back wall — splits around structural mid-post when present
        if _needs_mid_post:
            half_b = round((span_l - pw) / 2)
            parts.append(_part("wall_panel", qty=2,
                               note=f"Rückwand {half_b}×{panel_h} mm, {mat_label}"))
        else:
            parts.append(_part("wall_panel", qty=1,
                               note=f"Rückwand {span_l}×{panel_h} mm, {mat_label}"))

        # Left + right walls — split when side span > 2500 mm
        if _needs_side_post:
            half_s = round((span_w - pw) / 2)
            parts.append(_part("wall_panel", qty=4,
                               note=f"Seitenwand {half_s}×{panel_h} mm, {mat_label}"))
            parts.append(_part("tube_100x100", qty=2, length_mm=panel_h,
                               note=f"Wandpfosten Seite {panel_h} mm"))
        else:
            parts.append(_part("wall_panel", qty=2,
                               note=f"Seitenwand {span_w}×{panel_h} mm, {mat_label}"))

        # Schienen: 12 total (4 per wall × 3 walls)
        #   6 vertical  (2 per wall) — all at panel_h
        #   2 horizontal back  — at span_l
        #   4 horizontal sides — at span_w
        parts.append(_part("schiene", qty=6, length_mm=panel_h,
                           note="Schiene vertikal 18×38mm"))
        parts.append(_part("schiene", qty=2, length_mm=span_l,
                           note="Schiene horizontal Rückwand 18×38mm"))
        parts.append(_part("schiene", qty=4, length_mm=span_w,
                           note="Schiene horizontal Seitenwand 18×38mm"))

    # ── Roller door ───────────────────────────────────────────────────────────
    if roller_door:
        parts.append(_part("roller_door", qty=1,
                           note=f"Breite {round(L - 2*o)} mm"))

    # ── Bike stands (always present) ──────────────────────────────────────────
    total_w = round(L - 2 * o)
    parts.append(_part("bike_stand_rail", qty=1, note=f"Breite {total_w} mm"))
    parts.append(_part("bike_stand",      qty=1, note=f"Breite {total_w} mm"))

    return parts
