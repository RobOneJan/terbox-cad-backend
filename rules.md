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
- Spans the inner top frame. Slopes toward the back (water runoff).
- Scaled along X to `L − 2 × o` and along Y to `W − 2 × o`.
- Top face sits just above the top tube center height.

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

### Panel dimensions (between tube inner faces)
- Clear height between tubes: `panel_h_inner = H − 2 × (o + tf) = H − 190 mm`
- Full wall: `panel_h = panel_h_inner`
- Half wall: `panel_h = panel_h_inner / 2`
- Panel Z center: `z_ctr = (o + tf) + panel_h / 2`
  - Full walls: `z_ctr = H / 2`
  - Half walls: `z_ctr = 95 + (H − 190) / 4`

### Panel positions
- Back wall: `back_y = W − o − tf − wt/2 = W − 110 mm` (panel front face flush with back tube inner face)
- Left wall: `left_x = o + tf + wt/2 = 110 mm`
- Right wall: `right_x = L − o − tf − wt/2 = L − 110 mm`

### Panel spans (clear between tube inner faces)
- Back wall span: `L − 2 × (o + tf) = L − 190 mm`
- Side wall span: `W − 2 × (o + tf) = W − 190 mm`

### Back wall split (middle post)
- When a structural middle post exists (`L > 2590 mm`), the back wall panel splits into two halves around the post.
- Half width: `(span − 100) / 2` where span = `L − 190`.
- No separate wall middle post is added when a structural middle post is present.

### Side wall split (no middle post equivalent)
- When side wall span > 2500 mm, split into two halves with a 100×100 middle post tube at the center.

---

## Schienen (C-channel rails)
- Vertical C-channel rails holding the wall panel edges in place.
- Simplified as solid boxes: 18 mm deep (into the room) × 38 mm wide × `panel_h` tall.
- **Two Schienen per wall face** — one at each vertical edge.
- Center position: aligned with the **tube center** (not the tube inner face).
  - Back wall: left Schiene at `x = o`, right at `x = L − o`, both at `y = back_y`.
  - Left wall: front Schiene at `y = o`, back at `y = W − o`, both at `x = left_x`.
  - Right wall: front Schiene at `y = o`, back at `y = W − o`, both at `x = right_x`.
- Color: steel grey (same as tubes and connectors).
- Added for all wall types (`full` and `half`) whenever walls are present.

---

## Roller Door
- Housing block (200 mm deep × 200 mm high) centered above the front opening.
- Width: `L − 2 × o` (full front opening width).
- Sits outside the front face of the box: `y = o − tf − housing_depth/2`.

## Bike Stand
- Mounting rail spanning the full box width, sitting on the floor inside the rear of the box.
- Individual stand units spaced at ≥ 750 mm intervals, count = `floor((L − 2 × o) / 750)`.
