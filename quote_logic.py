import math
from typing import List
from models import BoxConfig, BoxAngebotPreise, AngebotPosition, WallHeight

# ── Display-name maps ─────────────────────────────────────────────────────────

_FRAME_COLOR_NAMES = {
    "tiefschwarz":      "RAL 9005 Tiefschwarz",
    "verkehrsweiss":    "RAL 9016 Verkehrsweiß",
    "anthrazitgrau":    "RAL 7016 Anthrazitgrau",
    "lichtgrau":        "RAL 7035 Lichtgrau",
    "feuerrot":         "RAL 3000 Feuerrot",
    "enzianblau":       "RAL 5010 Enzianblau",
    "moosgruen":        "RAL 6005 Moosgrün",
    "schokoladenbraun": "RAL 8017 Schokoladenbraun",
}

_WPC_COLOR_NAMES = {
    "cedar":     "Zeder",
    "darkGrey":  "Dunkelgrau",
    "teak":      "Teak",
    "ipe":       "Ipe",
    "lightGrey": "Hellgrau",
}

_WALL_MAT_NAMES = {
    "wpc":                  "WPC Holzoptik",
    "realWood":             "Holz",
    "glass":                "Glas",
    "meshFence":            "Doppelstabmattenzaun",
    "meshFenceWithPrivacy": "Doppelstabmattenzaun mit Sichtschutz",
    "corrugatedSheet":      "Trapezblech",
}

_FLOOR_MAT_NAMES = {
    "wpcFloor":  "WPC Bodenbelag",
    "woodFloor": "Holzboden",
}

_ROLLER_DOOR_COLOR_NAMES = {
    "ral9005": "RAL 9005 Schwarz",
    "ral9016": "RAL 9016 Weiß",
    "ral7016": "RAL 7016 Anthrazitgrau",
    "ral7035": "RAL 7035 Lichtgrau",
    "ral3000": "RAL 3000 Feuerrot",
    "ral5010": "RAL 5010 Enzianblau",
    "ral6005": "RAL 6005 Moosgrün",
    "ral8017": "RAL 8017 Schokoladenbraun",
}

_o = 45.0   # tube cross-section offset (mm)


def box_config_to_positionen(
    config: BoxConfig,
    preise: BoxAngebotPreise,
) -> List[AngebotPosition]:
    """Translate a BoxConfig + price table into a list of AngebotPositions."""

    L, W, H = config.width_mm, config.depth_mm, config.height_mm
    positions: List[AngebotPosition] = []

    fc_name = _FRAME_COLOR_NAMES.get(
        config.frame_color.value if config.frame_color else "",
        "verzinkter Stahl",
    )

    # ── 1. Grundkörper ────────────────────────────────────────────────────────
    if preise.grundkorpus is not None:
        lines = [
            "Grundkorpus",
            f"{L/1000:.2f} m lang, {W/1000:.2f} m tief, {H/1000:.2f} m hoch",
            f"verzinkter Stahl, {fc_name} beschichtet",
        ]
        if config.with_roof:
            lines.append("inklusive Dach und Dachrinne")
        if not config.with_floor:
            lines.append("ohne Bodenplatte")
        positions.append(AngebotPosition(
            beschreibung="\n".join(lines),
            menge=1.0, einheit="Stk",
            einzelpreis=preise.grundkorpus,
        ))

    # ── 2. Wandsystem ─────────────────────────────────────────────────────────
    if preise.wand is not None and config.walls != WallHeight.none and config.wall_material:
        mat = config.wall_material.value
        mat_name = _WALL_MAT_NAMES.get(mat, mat)
        wall_h_mm = (H - 2 * _o) / 2 if config.walls == WallHeight.half else H - 2 * _o
        # Back wall + 2 side walls
        area_m2 = ((L - 2 * _o) + 2 * (W - 2 * _o)) * wall_h_mm / 1e6
        lines = [mat_name]
        if mat == "wpc" and config.wall_wpc_color:
            lines.append(f"Farbe {_WPC_COLOR_NAMES.get(config.wall_wpc_color.value, config.wall_wpc_color.value)}")
        if config.walls == WallHeight.half:
            lines.append(f"Halbhoch – {wall_h_mm/1000:.2f} m Wandhöhe")
        else:
            lines.append(f"Vollhoch – {wall_h_mm/1000:.2f} m Wandhöhe")
        lines.append(f"3 Wände (hinten + 2 Seiten), ca. {area_m2:.1f} m²")
        positions.append(AngebotPosition(
            beschreibung="\n".join(lines),
            menge=1.0, einheit="Stk",
            einzelpreis=preise.wand,
        ))

    # ── 3. Boden ──────────────────────────────────────────────────────────────
    if preise.boden is not None and config.with_floor:
        floor_area = (L - 2 * _o) * (W - 2 * _o) / 1e6
        mat_name = _FLOOR_MAT_NAMES.get(
            config.floor_material.value if config.floor_material else "",
            "Boden",
        )
        lines = [mat_name]
        if config.floor_material and config.floor_material.value == "wpcFloor" and config.floor_wpc_color:
            lines.append(f"Farbe {_WPC_COLOR_NAMES.get(config.floor_wpc_color.value, config.floor_wpc_color.value)}")
        lines.append(f"{(L - 2*_o)/1000:.2f} m × {(W - 2*_o)/1000:.2f} m, ca. {floor_area:.1f} m²")
        positions.append(AngebotPosition(
            beschreibung="\n".join(lines),
            menge=1.0, einheit="Stk",
            einzelpreis=preise.boden,
        ))

    # ── 4. Rolltor ────────────────────────────────────────────────────────────
    if preise.rolltor is not None and config.roller_door:
        door_w = (L - 2 * _o) / 1000
        lines = ["Rolltor", f"Breite {door_w:.2f} m"]
        if config.roller_door_color:
            lines.append(_ROLLER_DOOR_COLOR_NAMES.get(config.roller_door_color, config.roller_door_color.upper()))
        positions.append(AngebotPosition(
            beschreibung="\n".join(lines),
            menge=1.0, einheit="Stk",
            einzelpreis=preise.rolltor,
        ))

    # ── 5. Fahrradständer ─────────────────────────────────────────────────────
    if preise.fahrradstaender is not None and config.with_bike_stand:
        inner_span = L - 2 * _o
        n_racks = max(2, round(inner_span / 767.0))
        lines = [
            "Fahrradbügel",
            "zum Abschließen der Fahrräder",
            f"verzinkter Stahl, {fc_name} beschichtet",
        ]
        positions.append(AngebotPosition(
            beschreibung="\n".join(lines),
            menge=float(n_racks), einheit="Stk",
            einzelpreis=preise.fahrradstaender,
        ))

    # ── 6. Solar ──────────────────────────────────────────────────────────────
    if preise.solar is not None and config.with_solar and config.with_roof:
        _SW, _SD, _GAP = 760.0, 1530.0, 20.0
        inner_x = L - 2 * _o
        inner_y = W - 2 * _o
        if inner_y >= _SD + 100.0:
            panel_w = _SW
        elif inner_y >= _SW + 100.0:
            panel_w = _SD
        else:
            panel_w = 0.0
        n_solar = max(1, int(inner_x / (panel_w + _GAP))) if panel_w > 0 else 0
        if n_solar > 0:
            lines = [
                "Solaranlage",
                "Solarmodule 760 × 1530 mm (PV ST SOLAR)",
                f"Montage auf dem Dach, {n_solar} Module",
            ]
            if preise.solar_pro_panel:
                positions.append(AngebotPosition(
                    beschreibung="\n".join(lines),
                    menge=float(n_solar), einheit="Stk",
                    einzelpreis=preise.solar,
                ))
            else:
                positions.append(AngebotPosition(
                    beschreibung="\n".join(lines),
                    menge=1.0, einheit="Stk",
                    einzelpreis=preise.solar,
                ))

    # ── 7. Extras ─────────────────────────────────────────────────────────────
    positions.extend(preise.extras)

    # ── 8. Lieferkosten ───────────────────────────────────────────────────────
    if preise.lieferkosten is not None:
        positions.append(AngebotPosition(
            beschreibung="Lieferkosten",
            menge=1.0, einheit="Stk",
            einzelpreis=preise.lieferkosten,
        ))

    return positions
