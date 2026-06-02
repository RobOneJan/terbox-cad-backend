# TER BOX AB1000 – Assembly Rules

## Key Dimensions
- `a = 120 mm` — arm length of every connector (Y-Ecke, L-Ecke, T-Ecke)
- `o = a − 75 = 45 mm` — tube cross-section center offset from junction center in each perpendicular axis
- `tf = 50 mm` — tube half-width (100 mm tube → 50 mm each side from center)
- `o + tf = 95 mm` — distance from box outer edge to tube inner face
- All dimensions in millimeters.

## Maximum Box Dimensions
Values exceeding these are silently clamped (no error):
| Parameter | Maximum |
|-----------|---------|
| `length_mm` | 12 000 mm (12 m) |
| `width_mm` | 2 500 mm (2.5 m) |
| `height_mm` | 3 000 mm (3 m) |

---

## Y-Ecke (3-arm corner connector)
- Fixed geometry: 240×240×240 mm. Never scaled.
- Junction center = bbox center of the connector.
- 3 arms, each 120 mm long. Each arm points inward along one box axis (X, Y, or Z).
- Arm opening center is 75 mm from the junction center in each perpendicular direction.
- Used at all 8 box corners where three tubes meet.
- Placed so the junction center sits at (a, a, a) / (L−a, a, a) etc. — 120 mm inward from each corner.
- Front-bottom corners (0,0,0) and (1,0,0) are replaced by L-Ecke when `with_floor = false`.

## L-Ecke (2-arm corner connector)
- Fixed geometry. Two arms only: Y arm and Z arm (no X arm).
- Arm opening centers follow the same 75 mm rule as Y-Ecke.
- Used at front-bottom-left and front-bottom-right corners **only when `with_floor = false`** (no front bottom tube).
- Junction must be placed at `(o, a, a)` and `(L−o, a, a)` — **not** at `(a, a, a)`.
  - Reason: the L-Ecke has no X arm; its junction aligns with the tube cross-section center in X (= o = 45 mm), not the arm tip (= a = 120 mm).
- No flip or rotation required; arm mouths align correctly with tubes at (o, *, o) and (o, o, *) as loaded from the STEP file.

## T-Ecke (T-shaped connector)
- Fixed geometry. Two X arms + one Z arm (T-shape in the XZ plane).
- Used at the **top of each middle post** (front and back).
- The STEP template has the Z arm pointing **upward (+Z)**. At the post top, the Z arm must point **downward** (into the post) — apply a Z-flip: `z → −z`, and reverse face winding (`(a,b,c) → (a,c,b)`).
- After Z-flip, placed at `(post_x, y_pos, H−a)` so the Z arm descends into the post and both X arms align with the adjacent split top tubes.
- Total T-Ecke count = `2 × n_mid_posts` (one per post × front + back).

---

## Tubes (100×100 mm)
- Cross-section 100×100 mm. Length varies per position.
- Tube length = junction-center-to-junction-center distance minus 2× arm length (2 × 120 = 240 mm total).
- Tube cross-section center sits exactly at the arm opening center: `o = 45 mm` from junction in each perpendicular axis.
- Standard box: 12 tubes — 4 along X (length), 4 along Y (depth), 4 along Z (height).
- When `with_floor = false`: the front bottom X tube (at z = o, y = o) is omitted.
- When middle posts are present: the two top X tubes (front and back, at z = H−o) are each replaced by `n_mid_posts + 1` split segments.

### Split tubes (middle posts present)
- Segment spacing: `seg = (L − 2 × o) / (n_mid_posts + 1)`
- Post positions along X: `post_xs[i] = o + seg × (i + 1)` for i = 0…n−1
- Junction list: `[a] + post_xs + [L−a]`
- Each segment tube length: `x_right_junction − x_left_junction − 2 × a`
  - End segments (corner ↔ first/last T-Ecke): `seg − 2a − o`
  - Inner segments (T-Ecke ↔ T-Ecke): `seg − 2a`
- Segment centre X: `(x_left_junction + x_right_junction) / 2`
- Total split tubes: `2 × (n_mid_posts + 1)` (front and back top runs).

---

## Middle Posts (Mittelposten)
- Count: `n_mid_posts = max(0, ceil((L − 2 × o) / 2500) − 1)`
  - 0 posts when inner span ≤ 2500 mm
  - 1 post when inner span 2501–5000 mm
  - 2 posts when inner span 5001–7500 mm, etc.
- Evenly spaced: `post_xs[i] = o + seg × (i + 1)` where `seg = (L − 2 × o) / (n_mid_posts + 1)`
- **Two posts per X position**: one front (y = o), one back (y = W − o).
- Each post: standard 100×100 tube, length = `H − 2 × a`, centred at `(post_x, y_pos, H/2)`.
- T-Ecke connector at the top of each post at `(post_x, y_pos, H−a)` (Z-flipped).
- **Front posts only**: when `with_floor = false`, a Fussplatte is placed under each front middle post. Back posts always have the bottom horizontal tube as support.

---

## Fussplatte (Base Plate)
- Fixed geometry: 150×150×155 mm (pin + plate). Centered at bbox center.
- **Not placed at corners.** Used only under front middle posts when `with_floor = false`.
- **One per front middle post** — total count = `n_mid_posts` when no floor.
- Placement: translate so the bbox top (77.5 mm above center) sits at z = 0.
  - Effective center z = plate_top = 77.5 mm → `_place(bv, post_x, o, plate_top)` for each front post.
  - This puts the plate base at z = −77.5 mm and the pin tip at z = +77.5 mm (extending up into the tube bottom).
- One Fussplatte per front middle post when no floor.

---

## Roof
Two components — both always rendered when `with_roof = true`.

### Roof substructure (`Rohr Dach Links` — rendered as `Dach_Unterkonstruktion`)
- **Always present alongside the roof panel** — never omit it.
- STEP template piece: 1600 mm wide (X) × 1469 mm deep (Y) × 85 mm tall (Z).
- Contains **5 cross-beams** running in X, spaced **360 mm apart** in Y:
  - Beam centres at y ≈ 145, 505, 865, 1225, 1585 mm in the template.
  - Each beam ~30 mm wide (40×40 mm tube profile).
- Scaled in X to `L − 2 × o` and in Y to `W − 2 × o`. Beam spacing scales proportionally.
- Placed centre at `(L/2, W/2, H − o + t_sub/2)` — sits on top of the top frame tubes.
- Color: steel grey.

### Roof panel (`Dach Links` — rendered as `Dach`)
- Flat/slightly-sloped panel sitting over the substructure.
- STEP template piece: 1600 mm wide (X) × 1654 mm deep (Y) × 64 mm thick (Z).
- Scaled in X to `L − 2 × o` and in Y to `W − 2 × o`.
- Placed centre at `(L/2, W/2, H − o + t_panel/2)`.
- Color: steel grey.

---

## Floor
- Flat panel (planks or solid) spanning the inner bottom frame.
- Size: `(L − 2 × o) × (W − 2 × o)`. Thickness: 30 mm.
- Center: `(L/2, W/2, o)` — flush with the bottom tube center height.

---

## Walls
- Three walls: back, left, right. Front is always open.
- Height options: `full` (floor to ceiling between tubes), `half` (lower half only), `none`.
- Panel thickness: 30 mm.

### Panel dimensions (tube center to tube center)
- Panels span from tube center to tube center. The Schienen (mounted at tube centers) frame all 4 edges.
- Full wall height: `panel_h = H − 2 × o = H − 90 mm`
- Half wall height: `panel_h = (H − 2 × o) / 2`
- Panel Z center: `z_ctr = o + panel_h / 2`
  - Full walls: `z_ctr = H / 2`
  - Half walls: `z_ctr = o + (H − 2 × o) / 4`

### Panel face positions (face sits at tube center)
- Back wall: `back_y = W − o − wt/2` (panel back face at tube center y = W − o)
- Left wall: `left_x = o + wt/2` (panel left face at tube center x = o)
- Right wall: `right_x = L − o − wt/2`

### Panel spans (tube center to tube center)
- Back wall span: `L − 2 × o = L − 90 mm`
- Side wall span: `W − 2 × o = W − 90 mm`

### Back wall split (middle posts)
- When `n_mid_posts > 0`, the back wall splits into `n_mid_posts + 1` panels around the structural posts.
- Panel width: `(span_l − n_mid_posts × 100) / (n_mid_posts + 1)` where `span_l = L − 2 × o`.
- No separate wall post is added — the structural mid-post tube serves as the divider.

### Side wall split (side posts)
- `n_side_posts = max(0, ceil((W − 2 × o) / 2500) − 1)` — same every-2500mm rule as length.
- When `n_side_posts > 0`, each side wall splits into `n_side_posts + 1` panels, each with a 100×100 post tube as divider.

---

## Schienen (C-channel rails)
- C-channel rails mounted centered on the surrounding tubes, fully framing each panel on all 4 sides.
- Simplified as solid boxes: 18 mm deep × 38 mm wide (≥ panel thickness).
- **4 Schienen per wall face**: 2 vertical (left + right edges) + 2 horizontal (bottom + top edges).
- All Schienen centered on the tube center axis — the panel edges terminate at the tube center, inside the Schiene groove.

### Back wall Schienen
| Rail | Dimensions | Center position |
|------|-----------|-----------------|
| Left vertical | `18 × 38 × panel_h` | `(o, back_y, z_ctr)` |
| Right vertical | `18 × 38 × panel_h` | `(L−o, back_y, z_ctr)` |
| Bottom horizontal | `(L−2o) × 38 × 18` | `(L/2, back_y, o)` |
| Top horizontal | `(L−2o) × 38 × 18` | `(L/2, back_y, H−o)` |

### Left wall Schienen
| Rail | Dimensions | Center position |
|------|-----------|-----------------|
| Front vertical | `38 × 18 × panel_h` | `(left_x, o, z_ctr)` |
| Back vertical | `38 × 18 × panel_h` | `(left_x, W−o, z_ctr)` |
| Bottom horizontal | `38 × (W−2o) × 18` | `(left_x, W/2, o)` |
| Top horizontal | `38 × (W−2o) × 18` | `(left_x, W/2, H−o)` |

### Right wall: same pattern as left wall at `x = right_x`.

- Color: steel grey (same as tubes and connectors).
- Added for all wall types (`full` and `half`) whenever walls are present.

---

## Roller Door
- Housing block (200 mm deep × 200 mm high) centered above the front opening.
- Width: `L − 2 × o` (full front opening width).
- Sits outside the front face of the box: `y = o − tf − housing_depth/2`.

## Bike Stand
- **Always present** — not a configurable option, rendered for every box.
- Two components from the TER BOX 100×100 STEP file (`Fahrradständer 40*40` and `Fahrradständer Befestigung`).

### Connecting bar (`Fahrradstaender_Halterung`)
- A **40×40 mm square tube** spanning the full inner length `L − 2 × o`, running in X at the back wall.
- Generated procedurally with `_make_tube_box("x", inner_span, width=40.0)` — not scaled from STEP.
- Position:
  - X centre: `L / 2`
  - Y centre: `cy_s + 220` — flush with the back face of the P-arm mounting slots
  - Z centre: `cz_s + 360` — arm-tip height (derived from STEP template offsets)
- `cy_s = W − (o + 50) − 240`, `cz_s = o + rack_height / 2` (rack height = 759 mm from STEP).

### P-shaped rack units (`Fahrradstaender_0 … N`)
- The STEP element `Fahrradständer 40*40` contains **3 rack units side by side** (total X span = 2300 mm, natural pitch = 767 mm).
- **Extract the centre unit** (vertices with `−268 < x < 304` in the centred element frame; 144 verts, 92 faces). This gives the full P-shape in the Y-Z plane at 40 mm wide in X.
- **Do not scale** the extracted unit. Each instance is placed at its natural size.
- Number of units: `n_racks = max(2, round((L − 2 × o) / 767))`
- Spacing: equal margins at both ends — `pitch = (L − 2 × o) / (n_racks + 1)`
- X positions: `cx_i = o + pitch × (i + 1)` for i = 0 … n_racks − 1
- Y centre: `cy_s = W − (o + 50) − 240`
- Z centre: `cz_s = o + 759 / 2 ≈ o + 379.5`

---

## Technische Vorgaben

### U-Profile (Schienen)
| Material | Profil | Außenmaß | Materialstärke |
|----------|--------|-----------|----------------|
| Holz | 35 × 35 × 35 mm | 35 mm | 3 mm |
| WPC  | 25 × 25 × 25 mm | 25 mm | 2 mm |

- **Obere und untere U-Profile** werden durchgehend montiert (volle Spannbreite).
- **Seitliche U-Profile** erhalten Abstand an den Enden, sodass sie sich nicht mit den horizontalen Profilen kreuzen oder überschneiden.

### Querbalken
- Im oberen Bereich ist **alle 450 mm** ein Querbalken vorzusehen.
- Querbalken laufen in Y-Richtung (Tiefe), gleichmäßig über die Länge verteilt.
- Anzahl: `n = ceil(span_l / 450)` wobei `span_l = L − 2 × o`
- Länge pro Querbalken: `span_w = W − 2 × o`

### Füllungen (Wandelemente)
| Material | Höhe pro Element | Materialstärke |
|----------|-----------------|----------------|
| Holz | 150 mm | 28 mm |
| WPC  | 150 mm | 21 mm |

### Bohrungen
| Typ | Durchmesser |
|-----|-------------|
| Eckbohrungen | 15 mm |
| Rohrbohrungen | 12 mm |

### Dachrinne
- Standardlänge: **2000 mm** pro Abschnitt.
- Anzahl Abschnitte: `n = ceil(gutter_span / 2000)` wobei `gutter_span = L − 2 × o`
- Verbindungsstücke: `n − 1` (bei mehreren Abschnitten)
- Endkappen: immer **2** (links und rechts)
- Fallrohr: immer **1**

### Zusätzliche Pfeiler (Mittelpfosten)
Gleiche Logik wie Mittelpost, aber mit tiefenabhängigem Schwellwert:

| Bedingung | Erster Pfeiler ab Länge |
|-----------|------------------------|
| `width_mm > 1500 mm` | `length_mm > 2500 mm` |
| `width_mm ≤ 1500 mm` | `length_mm > 3500 mm` |

- Folgeintervall bleibt **2500 mm** (wie Mittelpost-Regel).
- Formel: `first_threshold = 2500 if width_mm > 1500 else 3500`
- `n_mid_posts = max(0, ceil(max(0, inner_span_l − first_threshold) / 2500))`

### Befestigung der Elemente
| Wandtyp | Befestigungsart |
|---------|----------------|
| Doppelstabmattenzaun | Zaunelemente direkt an den Pfosten befestigt |
| Glaselemente | Klemmprofile an den Pfosten montiert |

- Klemmprofile für Glas: eines pro vertikalem Pfosten → `6 + 2 × n_mid_posts` Stück pro Box.
