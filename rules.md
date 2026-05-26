# TER BOX AB1000 – Assembly Rules

## Key Dimensions
- `a = 120 mm` — arm length of every connector (Y-Ecke, L-Ecke, T-Ecke)
- `o = a − 75 = 45 mm` — tube cross-section center offset from junction center in each perpendicular axis
- `tf = 50 mm` — tube half-width (100 mm tube → 50 mm each side from center)
- `o + tf = 95 mm` — distance from box outer edge to tube inner face
- All dimensions in millimeters.

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
- Used at the **top of each middle post** (front and back) when a middle post is present.
- The STEP template has the Z arm pointing **upward (+Z)**. At the post top, the Z arm must point **downward** (into the post) — apply a Z-flip: `z → −z`, and reverse face winding (`(a,b,c) → (a,c,b)`).
- After Z-flip, placed at `(L/2, y_pos, H−a)` so the Z arm descends into the post and both X arms align with the two split top tubes.

---

## Tubes (100×100 mm)
- Cross-section 100×100 mm. Length varies per position.
- Tube length = junction-center-to-junction-center distance minus 2× arm length (2 × 120 = 240 mm total).
- Tube cross-section center sits exactly at the arm opening center: `o = 45 mm` from junction in each perpendicular axis.
- Standard box: 12 tubes — 4 along X (length), 4 along Y (depth), 4 along Z (height).
- When `with_floor = false`: the front bottom X tube (at z = o, y = o) is omitted.
- When a middle post is present: the two top X tubes (front and back, at z = H−o) are each replaced by two half-length split tubes.

### Split tubes (middle post present)
- Each split tube: `half_len = L/2 − 3 × a`
- Left half center: `cx_left = (a + L/2) / 2`
- Right half center: `cx_right = (L/2 + L−a) / 2`
- Both sit at the same Z and Y positions as the original full top tubes.

---

## Middle Post (Mittelpost)
- Added when the inner length span exceeds 2500 mm: `L − 2 × o > 2500` (i.e., L > 2590 mm).
- Two posts: one front (y = o), one back (y = W − o).
- Post is a standard 100×100 tube, length = `H − 2 × a` (same as all vertical corner tubes).
- Post center: `(L/2, y_pos, H/2)`.
- T-Ecke connector sits at the top of each post at `(L/2, y_pos, H−a)` (Z-flipped).
- **Front post only**: when `with_floor = false`, a Fussplatte is placed under the front middle post. The back post always has the bottom horizontal tube as support.

---

## Fussplatte (Base Plate)
- Fixed geometry: 150×150×155 mm (pin + plate). Centered at bbox center.
- **Not placed at corners.** Used only under the front middle post when `with_floor = false`.
- Placement: translate so the bbox top (77.5 mm above center) sits at z = 0.
  - Effective center z = plate_top = 77.5 mm → `_place(bv, L/2, o, plate_top)`.
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

### Back wall split (middle post)
- When a structural middle post exists (`L > 2590 mm`), the back wall panel splits into two halves around the post.
- Half width: `(span − 100) / 2` where span = `L − 190`.
- No separate wall middle post is added when a structural middle post is present.

### Side wall split (no middle post equivalent)
- When side wall span > 2500 mm, split into two halves with a 100×100 middle post tube at the center.

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
- Two components from the TER BOX 100×100 STEP file:
  1. **Mounting rail** (`Fahrradständer Befestigung`): one piece, scaled in X to `total_w = L − 2 × o`, centered at `(L/2, W − (o + 50) − 22, o + rail_height/2)`.
  2. **Stand assembly** (`Fahrradständer 40*40`): one piece, scaled in X to `total_w`. The STEP component is 2300 mm wide (full template-box assembly). Scaling it proportionally to `total_w` preserves the internal slot geometry.
- Both pieces share the same Y and Z positions; the stand assembly sits just in front of the mounting rail near the back wall.
- The STEP stand assembly contains ~3 bike slots at ~767 mm spacing in the 2300 mm template. Scaled to any box width, slot spacing = `total_w / 3` approximately.
- Minimum useful box width: 750 mm clear span — any standard box satisfies this.
- Do **not** replicate the stand assembly n times. Scale once to `total_w` and place as a single instance.
