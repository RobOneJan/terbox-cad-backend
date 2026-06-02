import json
import math
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
    inner_span_l     = L - 2 * o
    inner_span_w     = W - 2 * o
    # Mid-post threshold depends on box depth:
    #   depth > 1500 mm → first post from length > 2500 mm
    #   depth ≤ 1500 mm → first post from length > 3500 mm
    # Subsequent posts every 2500 mm in both cases.
    first_threshold  = 2500.0 if width_mm > 1500.0 else 3500.0
    n_mid_posts      = max(0, math.ceil(max(0.0, inner_span_l - first_threshold) / 2500.0))
    n_side_posts     = max(0, math.ceil(inner_span_w / 2500.0) - 1)

    inner_l = round(L - 2 * a)
    inner_w = round(W - 2 * a)
    inner_h = round(H - 2 * a)

    # ── Connectors ───────────────────────────────────────────────────────────
    # Without floor: front-bottom two Y-Ecke become L-Ecke (no X arm)
    n_y = 8 if with_floor else 6
    n_l = 0 if with_floor else 2
    n_t = 2 * n_mid_posts   # one T-Ecke per mid-post × front + back

    parts: List[dict] = []
    parts.append(_part("y_corner", qty=n_y))
    if n_l:
        parts.append(_part("l_corner", qty=n_l))
    if n_t:
        parts.append(_part("t_corner", qty=n_t))

    # ── Tubes ─────────────────────────────────────────────────────────────────
    # X (length) — 4 runs: front-bottom, back-bottom, front-top, back-top
    #   front-bottom omitted when no floor
    #   front-top + back-top each split into (n_mid_posts+1) segments when posts present
    n_x_bottom = (2 if with_floor else 1)   # back-bottom always, front-bottom only with floor
    if n_x_bottom > 0:
        parts.append(_part("tube_100x100", qty=n_x_bottom, length_mm=inner_l,
                           note=f"Längsträger unten {inner_l} mm"))

    if n_mid_posts == 0:
        parts.append(_part("tube_100x100", qty=2, length_mm=inner_l,
                           note=f"Längsträger oben {inner_l} mm"))
    else:
        _seg      = inner_span_l / (n_mid_posts + 1)
        end_len   = round(_seg - 2 * a - o)        # corner → first/last T-Ecke
        inner_len = round(_seg - 2 * a)             # T-Ecke → T-Ecke
        n_end_segs   = 4                             # 2 ends × front + back
        n_inner_segs = 2 * (n_mid_posts - 1)        # inner gaps × front + back
        parts.append(_part("tube_100x100", qty=n_end_segs, length_mm=end_len,
                           note=f"Längsträger oben Rand {end_len} mm"))
        if n_inner_segs > 0:
            parts.append(_part("tube_100x100", qty=n_inner_segs, length_mm=inner_len,
                               note=f"Längsträger oben Mitte {inner_len} mm"))

    # Y (depth)
    parts.append(_part("tube_100x100", qty=4, length_mm=inner_w,
                       note=f"Querträger {inner_w} mm"))

    # Z (height) — corner posts
    parts.append(_part("tube_100x100", qty=4, length_mm=inner_h,
                       note=f"Stützen {inner_h} mm"))

    # Mid-posts (front + back), one pair every 2500 mm
    if n_mid_posts > 0:
        parts.append(_part("tube_100x100", qty=2 * n_mid_posts, length_mm=inner_h,
                           note=f"Mittelpost {inner_h} mm"))
        if not with_floor:
            parts.append(_part("base_plate", qty=n_mid_posts,
                               note="Fußstück Mittelpost Vorne"))

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

        # Gutter (Dachrinne): standard section 2000 mm; extend with connectors for longer spans
        gutter_span = round(L - 2 * o)
        n_gutter    = math.ceil(gutter_span / 2000)
        parts.append(_part("gutter_section",    qty=n_gutter,       note=f"Dachrinne 2000 mm × {n_gutter}"))
        if n_gutter > 1:
            parts.append(_part("gutter_connector", qty=n_gutter - 1, note="Dachrinnen-Verbindungsstück"))
        parts.append(_part("gutter_end_cap",    qty=2,              note="Dachrinnen-Endkappe links + rechts"))
        parts.append(_part("downpipe",          qty=1,              note="Fallrohr"))

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
        # Panel thickness by material
        if wall_material == "realWood":
            wt_mm = 28
        elif wall_material == "wpc":
            wt_mm = 21
        else:
            wt_mm = 30

        # Back wall — split into (n_mid_posts+1) panels around structural mid-posts
        if n_mid_posts > 0:
            panel_w_b = round((span_l - n_mid_posts * pw) / (n_mid_posts + 1))
            parts.append(_part("wall_panel", qty=n_mid_posts + 1,
                               note=f"Rückwand {panel_w_b}×{panel_h}×{wt_mm} mm, {mat_label}"))
        else:
            parts.append(_part("wall_panel", qty=1,
                               note=f"Rückwand {span_l}×{panel_h}×{wt_mm} mm, {mat_label}"))

        # Left + right walls — split every 2500 mm
        if n_side_posts > 0:
            panel_w_s = round((span_w - n_side_posts * pw) / (n_side_posts + 1))
            parts.append(_part("wall_panel", qty=2 * (n_side_posts + 1),
                               note=f"Seitenwand {panel_w_s}×{panel_h}×{wt_mm} mm, {mat_label}"))
            parts.append(_part("tube_100x100", qty=2 * n_side_posts, length_mm=panel_h,
                               note=f"Wandpfosten Seite {panel_h} mm"))
        else:
            parts.append(_part("wall_panel", qty=2,
                               note=f"Seitenwand {span_w}×{panel_h}×{wt_mm} mm, {mat_label}"))

        # Schienen (U-Profile): dimensions depend on material
        #   Wood:  35×35×35×3 mm   WPC: 25×25×25×2 mm
        #   Upper + lower U-profiles run the full span (continuous).
        #   Side U-profiles are cut short to avoid overlap with top/bottom profiles.
        if wall_material in ("realWood",):
            schiene_spec = "35×35×35×3 mm (Holz)"
        elif wall_material in ("wpc",):
            schiene_spec = "25×25×25×2 mm (WPC)"
        else:
            schiene_spec = "U-Profil"
        # 4 per wall × 3 walls = 12 total
        parts.append(_part("schiene", qty=6, length_mm=panel_h,
                           note=f"Schiene vertikal {schiene_spec}"))
        parts.append(_part("schiene", qty=2, length_mm=span_l,
                           note=f"Schiene horizontal Rückwand {schiene_spec}"))
        parts.append(_part("schiene", qty=4, length_mm=span_w,
                           note=f"Schiene horizontal Seitenwand {schiene_spec}"))

        # Querbalken: one cross beam every 450 mm in the upper area, spanning box depth
        n_crossbeams = math.ceil(span_l / 450)
        parts.append(_part("crossbeam", qty=n_crossbeams, length_mm=span_w,
                           note=f"Querbalken alle 450 mm, {n_crossbeams} × {span_w} mm"))

        # Glass clamping profiles (Klemmprofile) — one per vertical post for glass walls
        if wall_material == "glass":
            n_clamp_posts = 6 + 2 * n_mid_posts   # 2 edge posts × 3 walls + 2 per mid-post
            parts.append(_part("glass_clamp_profile", qty=n_clamp_posts,
                               note="Klemmprofil für Glaselemente"))

    # ── Roller door ───────────────────────────────────────────────────────────
    if roller_door:
        parts.append(_part("roller_door", qty=1,
                           note=f"Breite {round(L - 2*o)} mm"))

    # ── Bike stands (always present) ──────────────────────────────────────────
    # One 40×40 mm connecting bar spanning the full inner length at arm-tip height.
    # N individual P-shaped rack units, natural pitch ≈ 767 mm, minimum 2.
    total_w  = round(inner_span_l)
    n_racks  = max(2, round(inner_span_l / 767.0))
    parts.append(_part("bike_stand_rail", qty=1, note=f"Querrohr 40×40 mm, Länge {total_w} mm"))
    parts.append(_part("bike_stand",      qty=n_racks, note=f"Fahrradhalter P-Form × {n_racks}"))

    return parts
