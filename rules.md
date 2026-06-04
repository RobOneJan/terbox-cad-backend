# TER BOX AB1000 – Assembly Rules

## Dimensions

| Parameter | Meaning | Max (clamped silently) |
|-----------|---------|------------------------|
| `width_mm` | Box width — main horizontal span; middle posts run along this axis | 12 000 mm |
| `depth_mm` | Box depth — shorter horizontal span; determines mid-post threshold | 2 500 mm |
| `height_mm` | Box height | 3 000 mm |

Internal aliases: `L = width_mm`, `W = depth_mm`, `H = height_mm`.

---

## Key Offsets

| Symbol | Value | Meaning |
|--------|-------|---------|
| `a` | 120 mm | Arm length of every connector (Y-Ecke, L-Ecke, T-Ecke) |
| `o = a − 75` | 45 mm | Tube cross-section centre from junction centre (each perpendicular axis) |
| `tf` | 50 mm | Tube half-width (100 mm tube) |
| `ti = o + tf` | 95 mm | Tube **inner** face from box origin |

---

## Y-Ecke (3-arm corner connector)

- Fixed geometry: 240×240×240 mm. Never scaled.
- Junction centre = bbox centre of the connector.
- 3 arms, each 120 mm long. Each arm points inward along one box axis (X, Y, or Z).
- Arm opening centre is 75 mm from the junction centre in each perpendicular direction.
- Used at all 8 box corners where three tubes meet.
- Placed so the junction centre sits at (a, a, a) / (L−a, a, a) etc. — 120 mm inward from each corner.
- Front-bottom corners (0,0,0) and (1,0,0) are replaced by L-Ecke when `with_floor = false`.

## L-Ecke (2-arm corner connector)

- Fixed geometry. Two arms only: Y arm and Z arm (no X arm).
- Used at front-bottom-left and front-bottom-right corners **only when `with_floor = false`**.
- Junction placed at `(o, a, a)` and `(L−o, a, a)` — not at `(a, a, a)`.

## T-Ecke (T-shaped connector)

- Fixed geometry. Two X arms + one Z arm.
- Used at **both the top and the bottom of each middle post** (front and back).

### T-Ecke top
- STEP template has Z arm pointing up → flip: `z → −z`, reverse face winding.
- Placed at `(post_x, y_pos, H−a)`.

### T-Ecke bottom
- No flip. Placed at `(post_x, y_pos, a)`.
- Back posts: always. Front posts: only when `with_floor = true`.

---

## Tubes (100×100 mm)

- Cross-section 100×100 mm. Tube length = junction-centre to junction-centre.
- Tube cross-section centre sits `o = 45 mm` from the junction centre in each perpendicular axis.
- Standard box: 12 tubes — 4 along X (width), 4 along Y (depth), 4 along Z (height).
- When `with_floor = false`: front bottom X tube is omitted.
- When `n_mid_posts > 0`: all four X tubes are replaced by split segments.

### Split tubes (middle posts present)

- Segment spacing: `seg = (L − 2 × o) / (n_mid_posts + 1)`
- Post positions along X: `post_xs[i] = o + seg × (i + 1)`
- Junction list: `[a] + post_xs + [L−a]`
- Each segment length = `x_right_junction − x_left_junction`
- Top splits placed at `z = H − o`; bottom splits at `z = o`.

---

## Middle Posts (Mittelposten)

Middle posts run along the **width** axis (X direction).

- Count: `n_mid_posts = max(0, ceil(max(0, inner_span − first_threshold) / 2500))`
  - `inner_span = L − 2 × o`
  - `first_threshold = 2500 if depth_mm > 1500 else 3500`
- Evenly spaced: `post_xs[i] = o + seg × (i + 1)` where `seg = (L − 2 × o) / (n_mid_posts + 1)`
- Two posts per X position: front (y = o) and back (y = W − o).

### Post height

| Condition | Length | Centre Z |
|-----------|--------|----------|
| Back post (always) | `H − 2 × a` | `H / 2` |
| Front post, `with_floor = true` | `H − 2 × a` | `H / 2` |
| Front post, `with_floor = false` | `H − 2 × a + 100` | `(H − 100) / 2` |

### Connectors per post

| Position | Connector | Placement |
|----------|-----------|-----------|
| Top | T-Ecke Z-flipped | `(post_x, y_pos, H−a)` |
| Bottom | T-Ecke unflipped | `(post_x, y_pos, a)` — back always; front only with floor |

---

## Fussplatte (Base Plate)

- Only under **front middle posts** when `with_floor = false`.
- Placement: bbox top at z = 0 → `_place(bv, post_x, o, plate_top)`.

---

## Roof

Rendered when `with_roof = true`. Always includes both substructure and panel.

### Roof substructure (`Dach_Unterkonstruktion`)
- Scaled in X to `L − 2 × o` and in Y to `W − 2 × o`.
- Centre: `(L/2, W/2, H − o + _SUB_CZ)` where `_SUB_CZ = −5.3 mm`.

### Roof panel (`Dach`)
- Scaled in X to `L − 2 × o` and in Y to `W − 2 × o`.
- Centre: `(L/2, W/2, H − o + _PANEL_CZ)` where `_PANEL_CZ = +7.2 mm`.

---

## Floor

- Flat panel spanning `(L − 2 × o) × (W − 2 × o)`. Thickness: 30 mm.
- Centre: `(L/2, W/2, o)`.
- Materials: `wpcFloor` (WPC planks), `woodFloor` (wood planks), or solid slab.

---

## Walls

- Three walls: back, left, right. Front is always open.
- Height options: `full`, `half`, `none`.
- Panel thickness by material: wood = 28 mm, WPC = 21 mm, others = 30 mm.

### Panel height

- Full wall: `panel_h = H − 2 × o`
- Half wall: `panel_h = (H − 2 × o) / 2`
- Z centre: `z_ctr = o + panel_h / 2`

### Panel perpendicular position (outer face = tube outer face, enclosed by tube)

Each panel's **outer face** is at the tube outer face. The panel extends inward — fully enclosed by the tube cross-section.

| Wall | Panel centre | Outer face |
|------|-------------|------------|
| Back  | `back_y  = (W − o + tf) − wt/2` | `W − o + tf = W + 5 mm` |
| Left  | `left_x  = (o − tf) + wt/2`     | `o − tf = −5 mm`        |
| Right | `right_x = (L − o + tf) − wt/2` | `L − o + tf = L + 5 mm` |

### Panel spans (between tube inner faces)

| Wall | Span direction | Length |
|------|---------------|--------|
| Back | X | `L − 2 × ti = L − 190 mm` |
| Left / Right | Y | `W − 2 × ti = W − 190 mm` |

where `ti = o + tf = 95 mm`.

### Back wall split (middle posts)

Panel segments start/end at `ti` / `L − ti` and each post edge.

### Side wall split (side posts)

- `n_side_posts = max(0, ceil((W − 2 × ti) / 2500) − 1)`
- Segment boundaries: `ti` → post edge → … → `W − ti`.

---

## Schienen (C-channel rails)

Mounted on **tube inner faces** (`ti = 95 mm` from each edge). Panel fits inside the Schiene groove.

### Dimensions by material

| Material | Depth `_sd` | Width `_sw` |
|----------|------------|------------|
| Holz | 35 mm | 35 mm |
| WPC | 25 mm | 25 mm |
| Others | 18 mm | 38 mm |

### Back wall Schienen

| Rail | Dimensions | Centre position |
|------|-----------|-----------------|
| Left vertical | `_sd × _sw × panel_h` | `(ti, back_y, z_ctr)` |
| Right vertical | `_sd × _sw × panel_h` | `(L−ti, back_y, z_ctr)` |
| Bottom horizontal | `(L−2·ti) × _sw × _sd` | `(L/2, back_y, o)` |
| Top horizontal | `(L−2·ti) × _sw × _sd` | `(L/2, back_y, H−o)` |

### Left wall Schienen

| Rail | Dimensions | Centre position |
|------|-----------|-----------------|
| Front vertical | `_sw × _sd × panel_h` | `(left_x, ti, z_ctr)` |
| Back vertical | `_sw × _sd × panel_h` | `(left_x, W−ti, z_ctr)` |
| Bottom horizontal | `_sw × (W−2·ti) × _sd` | `(left_x, W/2, o)` |
| Top horizontal | `_sw × (W−2·ti) × _sd` | `(left_x, W/2, H−o)` |

### Right wall: same pattern at `x = right_x`.

---

## Roller Door

- Optional (`roller_door = true`).
- Housing block 200 mm deep × 200 mm high, width `L − 2 × o`.
- Sits outside the front face: `y = o − tf − 100`, `z = H − o − 100`.
- `roller_door_color`: RAL code for the door; falls back to `frame_color` if not set.

---

## Frame Color (`frame_color`)

All structural steel — connectors, tubes, middle posts, roof substructure, bolts, Schienen, roller-door housing — share one configurable color. Default: steel grey `(0.68, 0.68, 0.70)`.

| API value | Display name | RAL |
|-----------|--------------|-----|
| `tiefschwarz` | Tiefschwarz | 9005 |
| `verkehrsweiss` | Verkehrsweiß | 9016 |
| `anthrazitgrau` | Anthrazitgrau | 7016 |
| `lichtgrau` | Lichtgrau | 7035 |
| `feuerrot` | Feuerrot | 3000 |
| `enzianblau` | Enzianblau | 5010 |
| `moosgruen` | Moosgrün | 6005 |
| `schokoladenbraun` | Schokoladenbraun | 8017 |

---

## Bike Stand (`with_bike_stand`)

- Optional — default `true`.
- When `false`: neither rack units nor connecting bar are rendered or added to the BOM or Angebot.
- Components from `TER BOX 100×100.step`: `Fahrradständer 40*40` + `Fahrradständer Befestigung`.

### Connecting bar (`Fahrradstaender_Halterung`)
- 40×40 mm square tube, length = `L − 2 × o`, running in X.
- Centre: `(L/2, cy_s + 220, cz_s + 360)`.

### P-shaped rack units
- `n_racks = max(2, round((L − 2 × o) / 767))`
- Evenly spaced along X with equal end margins: `pitch = (L − 2 × o) / (n_racks + 1)`
- Y centre: `cy_s = W − (o + 50) − 240`
- Z centre: `cz_s = o + rack_height / 2` (rack height ≈ 759 mm from STEP)

---

## Solar Panels (`with_solar`)

- Requires `with_roof = true`. Default `false`.
- Source: `PV ST SOLAR.step` — monolithic solid, 760 × 35.2 × 1530 mm (W × T × L in STEP).
- Laid flat by rotating `(x,y,z)→(x,z,y)`; face winding reversed.

### Orientation (auto-selected by depth)

| Condition | Panel W (along box X) | Panel D (along box Y) |
|-----------|-----------------------|-----------------------|
| `depth_mm − 2·o ≥ 1630` | 760 mm | 1530 mm |
| `depth_mm − 2·o ≥ 860` | 1530 mm (rotated 90°) | 760 mm |
| Otherwise | no panels | — |

### Count and spacing
- `n_solar = max(1, floor(inner_x / (panel_w + 20)))` where `inner_x = L − 2 × o`
- 20 mm gap between panels; centred along X and Y.
- Panel Z centre: `H − o + 25 + 17.6 mm` (bottom face on roof surface).

### Mounting rails
- 2 aluminium rails per panel (40 × 25 mm), running along panel depth, at ±panel_w/4 in X.

---

## API Endpoints

Three routes, all require `X-API-Key` header.

| Method | Path | Returns |
|--------|------|---------|
| `POST` | `/ab1000/preview` | GLB binary (`model/gltf-binary`) |
| `POST` | `/ab1000/bom-xlsx` | Excel XLSX (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`) |
| `POST` | `/ab1000/angebot-konfiguration` | PDF (`application/pdf`) |

All three accept the same `BoxConfig` base (preview and bom-xlsx directly; angebot-konfiguration embeds it in `BoxAngebotRequest`).

### `BoxConfig` fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `width_mm` | float | required | Box width (main axis, ≤ 12 000 mm) |
| `depth_mm` | float | required | Box depth (≤ 2 500 mm) |
| `height_mm` | float | required | Box height (≤ 3 000 mm) |
| `with_roof` | bool | `true` | Include roof |
| `with_floor` | bool | `true` | Include floor |
| `walls` | enum | `"full"` | `"full"` \| `"half"` \| `"none"` |
| `wall_material` | enum\|null | `null` | `"wpc"` \| `"realWood"` \| `"glass"` \| `"meshFence"` \| `"meshFenceWithPrivacy"` \| `"corrugatedSheet"` |
| `wall_wpc_color` | enum\|null | `null` | `"cedar"` \| `"darkGrey"` \| `"teak"` \| `"ipe"` \| `"lightGrey"` |
| `floor_material` | enum\|null | `null` | `"wpcFloor"` \| `"woodFloor"` |
| `floor_wpc_color` | enum\|null | `null` | WPC color (see above) |
| `roller_door` | bool | `false` | Include roller door |
| `roller_door_color` | string\|null | `null` | RAL code e.g. `"ral9005"` |
| `with_solar` | bool | `false` | Solar panels on roof |
| `with_bike_stand` | bool | `true` | Bike rack system |
| `frame_color` | FrameColor\|null | `null` | Steel frame RAL color (see table above) |

### `/ab1000/angebot-konfiguration` additional fields (`BoxAngebotRequest`)

Embeds `config: BoxConfig` plus customer info and `preise: BoxAngebotPreise`.

#### `BoxAngebotPreise`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `grundkorpus` | float\|null | `null` | Steel frame + roof price |
| `wand` | float\|null | `null` | Complete wall system price |
| `boden` | float\|null | `null` | Floor panel price |
| `rolltor` | float\|null | `null` | Roller door price |
| `fahrradstaender` | float\|null | `null` | Bike stand price per rack (requires `with_bike_stand = true`) |
| `solar` | float\|null | `null` | Solar panel price |
| `solar_pro_panel` | bool | `false` | If `true`, solar price is per panel |
| `lieferkosten` | float\|null | `null` | Delivery price |
| `extras` | AngebotPosition[] | `[]` | Additional free-form positions |

---

## Technische Vorgaben

### U-Profile (Schienen)

| Material | Profil | Materialstärke |
|----------|--------|----------------|
| Holz | 35 × 35 × 35 mm | 3 mm |
| WPC | 25 × 25 × 25 mm | 2 mm |

### Querbalken

- Im oberen Bereich alle 450 mm ein Querbalken.
- Anzahl: `n = ceil((L − 2 × o) / 450)`
- Länge: `W − 2 × o`

### Füllungen (Wandelemente)

| Material | Höhe pro Element | Materialstärke |
|----------|-----------------|----------------|
| Holz | 150 mm | 28 mm |
| WPC | 150 mm | 21 mm |

### Dachrinne

- Standardlänge 2 000 mm pro Abschnitt.
- Anzahl: `n = ceil((L − 2 × o) / 2000)`
- Verbindungsstücke: `n − 1`, Endkappen: 2, Fallrohr: 1.

### Mittelpfosten — Schwellwert

| Bedingung | Erster Pfeiler ab Breite |
|-----------|--------------------------|
| `depth_mm > 1500 mm` | `width_mm > 2500 mm` |
| `depth_mm ≤ 1500 mm` | `width_mm > 3500 mm` |

Folgeintervall: 2500 mm. Formel: `first_threshold = 2500 if depth_mm > 1500 else 3500`
