from pathlib import Path
from typing import Optional, Dict, Tuple, List
import json

from models import (
    TerBoxConfiguration, ComputedConfig,
    FloorOption, WallHeight, WallMaterial, ClosureType, FeatureKey,
)

_TEMPLATE_PATH    = Path(__file__).parent / "TER BOX 100x100.step"
_AB_TEMPLATE_PATH = Path(__file__).parent / "TER BOX AB1000.step"
_REGISTRY_PATH    = Path(__file__).parent / "component_registry.json"

_STANDARD_WIDTH_CM  = 249.4
_STANDARD_HEIGHT_CM = 230.0

# --- TER BOX 100x100 component groups ---

_FRAME = frozenset([
    "Einschiebling 100x100 Links Hinten", "Einschiebling vorn links",
    "Einschiebling vorne rechts", "Einschiebling hinten rechts", "Einschiebling oben ",
    "ROHR 100 * 100 * 3 2300", "ROHR 100*100*3 2100 Waagerecht",
    "ROHR 100*100*3 2100 Senkrecht",
])
_FLOOR      = frozenset(["Leiste unten für den Boden", "Balken unten", "Bretter unten"])
_ROOF       = frozenset(["Leisten Oben", "Balken oben", "Dach", "Dachrinne"])
_SIDE_WPC   = frozenset(["Bretter Seite", "U Profile Seite"])
_SIDE_FENCE = frozenset(["Zaun Seite"])
_REAR_WPC   = frozenset(["Bretter hinten "])
_REAR_FENCE = frozenset(["Zaun hinten"])
_DOOR       = frozenset(["Garagentor"])
_CHARGING   = frozenset(["Halterung Ladestation"])
_BIKE       = frozenset(["Fahrradständer Befestigung", "Fahrradständer 40*40"])

# --- AB1000 component groups ---

_AB_CONNECTORS = frozenset(["Y-Ecke", "K Ecke", "T Ecke", "L-Ecke"])
_AB_TUBES = frozenset([
    "ROHR oben vorne 165", "Rohr unten links 180", "Rohr vorne rechts 200",
    "Rohr mitte 210", "Rohr Oben Links 180", "Rohr Oben Mitte 180",
    "Rohr Oben Rechts 180", "Rohr Unten 165", "Rohr oben 165",
    "Rohr unten 180 rechts", "Rohr 2 Meter Einlassung",
    "Rohr 2000 hinten links", "Rohr 2000 hinten Mitte", "Rohr hinten Rechts",
])
_AB_ROOF = frozenset(["Rohr Dach Links", "Dach Links"])
_AB_BASE = frozenset(["Fussplatte"])

# Template bounding box (mm) — derived from STEP
_AB_L = 3595.7
_AB_W = 2143.0
_AB_H = 2208.5

# --- Color maps ---

_RAL_RGB = {
    "ral9005": (0.055, 0.055, 0.063),
    "ral9016": (0.969, 0.969, 0.949),
    "ral7016": (0.220, 0.243, 0.259),
    "ral7035": (0.839, 0.839, 0.816),
    "ral3000": (0.686, 0.169, 0.118),
    "ral5010": (0.055, 0.302, 0.643),
    "ral6005": (0.059, 0.263, 0.212),
    "ral8017": (0.267, 0.184, 0.161),
    "ral1021": (0.976, 0.659, 0.000),
    "ral2004": (0.957, 0.275, 0.067),
}
_WPC_RGB = {
    "cedar":     (0.694, 0.502, 0.357),
    "darkGrey":  (0.259, 0.259, 0.259),
    "teak":      (0.702, 0.533, 0.314),
    "ipe":       (0.314, 0.220, 0.149),
    "lightGrey": (0.682, 0.682, 0.682),
}
_DEFAULT_GREY = (0.5, 0.5, 0.5)
_STEEL_RGB    = (0.68, 0.68, 0.70)

_WALL_MAT_RGB = {
    "realWood":             (0.60, 0.45, 0.30),
    "glass":                (0.60, 0.75, 0.85),
    "meshFence":            (0.55, 0.55, 0.55),
    "meshFenceWithPrivacy": (0.45, 0.50, 0.48),
    "corrugatedSheet":      (0.72, 0.72, 0.75),
}


def _wall_rgb(material: str | None, wpc_color: str | None) -> tuple:
    if not material:
        return _DEFAULT_GREY
    if material == "wpc":
        return _WPC_RGB.get(wpc_color, _WPC_RGB["cedar"]) if wpc_color else _WPC_RGB["cedar"]
    return _WALL_MAT_RGB.get(material, _DEFAULT_GREY)


def _floor_rgb(material: str | None, wpc_color: str | None) -> tuple:
    if material == "wpcFloor":
        return _WPC_RGB.get(wpc_color, _WPC_RGB["cedar"]) if wpc_color else _WPC_RGB["cedar"]
    if material == "woodFloor":
        return (0.65, 0.48, 0.30)
    return (0.60, 0.50, 0.35)  # natural wood default


def _plank_instances(name_prefix: str, lx: float, ly: float, lz: float,
                     cx: float, cy: float, cz: float, base_rgb: tuple,
                     plank_h: float = 120.0, gap: float = 5.0) -> list:
    """Horizontal planks stacked in Z (wall height). Each plank tinted slightly differently."""
    results = []
    r0, g0, b0 = base_rgb
    z0 = cz - lz / 2
    i, z = 0, z0
    while z + plank_h <= cz + lz / 2 + 0.5:
        vary = ((i % 3) - 1) * 0.04
        rgb = (max(0.0, min(1.0, r0 + vary)), max(0.0, min(1.0, g0 + vary)), max(0.0, min(1.0, b0 + vary)))
        pv, pf = _make_box(lx, ly, plank_h)
        results.append((f"{name_prefix}_{i}", _place(pv, cx, cy, z + plank_h / 2), pf, rgb))
        z += plank_h + gap
        i += 1
    return results


def _rib_instances(name_prefix: str, lx: float, ly: float, lz: float,
                   cx: float, cy: float, cz: float, base_rgb: tuple,
                   axis: str = "x", rib_w: float = 40.0, gap: float = 8.0) -> list:
    """Vertical corrugated ribs along full height, stacked in 'axis' direction."""
    results = []
    r0, g0, b0 = base_rgb
    if axis == "x":
        pos0 = cx - lx / 2
        i, pos = 0, pos0
        while pos + rib_w <= cx + lx / 2 + 0.5:
            vary = (i % 2) * 0.06
            rgb = (min(1.0, r0 + vary), min(1.0, g0 + vary), min(1.0, b0 + vary))
            pv, pf = _make_box(rib_w, ly, lz)
            results.append((f"{name_prefix}_{i}", _place(pv, pos + rib_w / 2, cy, cz), pf, rgb))
            pos += rib_w + gap
            i += 1
    else:  # axis == "y"
        pos0 = cy - ly / 2
        i, pos = 0, pos0
        while pos + rib_w <= cy + ly / 2 + 0.5:
            vary = (i % 2) * 0.06
            rgb = (min(1.0, r0 + vary), min(1.0, g0 + vary), min(1.0, b0 + vary))
            pv, pf = _make_box(lx, rib_w, lz)
            results.append((f"{name_prefix}_{i}", _place(pv, cx, pos + rib_w / 2, cz), pf, rgb))
            pos += rib_w + gap
            i += 1
    return results


def _floor_plank_instances(name_prefix: str, lx: float, ly: float, lz: float,
                            cx: float, cy: float, cz: float, base_rgb: tuple,
                            plank_w: float = 120.0, gap: float = 5.0) -> list:
    """Floor planks running along X, stacked in Y (box depth direction)."""
    results = []
    r0, g0, b0 = base_rgb
    y0 = cy - ly / 2
    i, y = 0, y0
    while y + plank_w <= cy + ly / 2 + 0.5:
        vary = ((i % 3) - 1) * 0.04
        rgb = (max(0.0, min(1.0, r0 + vary)), max(0.0, min(1.0, g0 + vary)), max(0.0, min(1.0, b0 + vary)))
        pv, pf = _make_box(lx, plank_w, lz)
        results.append((f"{name_prefix}_{i}", _place(pv, cx, y + plank_w / 2, cz), pf, rgb))
        y += plank_w + gap
        i += 1
    return results


# --- Geometry helpers ---

def _long_axis(verts):
    xs=[v[0] for v in verts]; ys=[v[1] for v in verts]; zs=[v[2] for v in verts]
    spans={"x":max(xs)-min(xs),"y":max(ys)-min(ys),"z":max(zs)-min(zs)}
    return max(spans,key=spans.get)

def _center_bbox(verts):
    xs=[v[0] for v in verts]; ys=[v[1] for v in verts]; zs=[v[2] for v in verts]
    cx=(min(xs)+max(xs))/2; cy=(min(ys)+max(ys))/2; cz=(min(zs)+max(zs))/2
    return [(x-cx,y-cy,z-cz) for x,y,z in verts]


def _center_tube_body(verts, axis):
    """Center tube at its body cross-section center.
    The tube body is square (100x100mm). One perp axis sometimes has ~30mm of extra
    geometry (a protruding bracket/feature) that pulls the bbox center off by ~15mm.
    Fix: body_size = min(perp_spans); for the oversized axis, body_center = min + body_size/2."""
    if not verts:
        return verts
    xs=[v[0] for v in verts]; ys=[v[1] for v in verts]; zs=[v[2] for v in verts]
    spans = [max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs)]
    ai = {"x": 0, "y": 1, "z": 2}[axis]
    perp = [i for i in range(3) if i != ai]
    body_size = min(spans[p] for p in perp)
    centers = [
        (min(xs)+max(xs))/2,
        (min(ys)+max(ys))/2,
        (min(zs)+max(zs))/2,
    ]
    all_min = [min(xs), min(ys), min(zs)]
    for pi in perp:
        if spans[pi] > body_size * 1.1:          # extra geometry present on this axis
            centers[pi] = all_min[pi] + body_size / 2
    cx, cy, cz = centers
    return [(x-cx, y-cy, z-cz) for x, y, z in verts]

def _center_at(verts, tx, ty, tz):
    """Center geometry at the given connection point."""
    return [(x-tx, y-ty, z-tz) for x,y,z in verts]

def _scale_along(verts, axis, target_length):
    if not verts: return []
    coords=[v[{"x":0,"y":1,"z":2}[axis]] for v in verts]
    tl=max(coords)-min(coords)
    if tl<=0: return verts
    s=target_length/tl
    return [(x*s,y,z) if axis=="x" else (x,y*s,z) if axis=="y" else (x,y,z*s)
            for x,y,z in verts]


def _stretch_tube(verts, axis, target_length, stub_len):
    """Stretch tube to target_length, preserving stub_len end regions so bolt holes stay at fixed offsets from each tube end."""
    if not verts:
        return []
    ai = {"x": 0, "y": 1, "z": 2}[axis]
    coords = [v[ai] for v in verts]
    orig_len = max(coords) - min(coords)
    if orig_len <= 0:
        return verts
    # After _center_bbox the tube is centered at origin: spans -half_orig..+half_orig
    half_orig = orig_len / 2
    half_new = target_length / 2
    orig_mid_half = half_orig - stub_len
    new_mid_half = half_new - stub_len
    if orig_mid_half <= 0 or new_mid_half <= 0:
        return _scale_along(verts, axis, target_length)
    scale_mid = new_mid_half / orig_mid_half
    shift = half_new - half_orig
    result = []
    for v in verts:
        c = v[ai]
        if c < -orig_mid_half:
            new_c = c - shift      # end A stub: shift outward
        elif c > orig_mid_half:
            new_c = c + shift      # end B stub: shift outward
        else:
            new_c = c * scale_mid  # middle: scale uniformly
        v2 = list(v)
        v2[ai] = new_c
        result.append(tuple(v2))
    return result


def _place(verts, px, py, pz):
    return [(x+px,y+py,z+pz) for x,y,z in verts]


# Winding verified for right-handed (x,y,z): each face normal points outward.
_TUBE_FACES = [
    (0,3,2),(0,2,1),  # axis_min cap
    (4,5,6),(4,6,7),  # axis_max cap
    (0,7,3),(0,4,7),  # side
    (1,2,6),(1,6,5),  # side
    (0,1,5),(0,5,4),  # side
    (2,3,7),(2,7,6),  # side
]


def _make_tube_box(axis: str, length: float, width: float = 100.0):
    """Procedural 100×100mm square tube box, centered at origin, variable length.
    Cyclic axis permutation preserves right-handed winding so _TUBE_FACES stay valid."""
    h, w = length / 2, width / 2
    base = [(-h,-w,-w),(-h,+w,-w),(-h,+w,+w),(-h,-w,+w),
            (+h,-w,-w),(+h,+w,-w),(+h,+w,+w),(+h,-w,+w)]
    if axis == "x":
        verts = base
    elif axis == "y":
        verts = [(c, a, b) for a, b, c in base]  # (x,y,z)→(z,x,y): long axis becomes y
    else:  # z
        verts = [(b, c, a) for a, b, c in base]  # (x,y,z)→(y,z,x): long axis becomes z
    return verts, _TUBE_FACES


def _make_box(lx: float, ly: float, lz: float):
    """Solid box lx×ly×lz centered at origin. Uses same winding as _TUBE_FACES."""
    hx, hy, hz = lx/2, ly/2, lz/2
    verts = [(-hx,-hy,-hz),(-hx,+hy,-hz),(-hx,+hy,+hz),(-hx,-hy,+hz),
             (+hx,-hy,-hz),(+hx,+hy,-hz),(+hx,+hy,+hz),(+hx,-hy,+hz)]
    return verts, _TUBE_FACES

# --- Caches ---

_template_dims = None
_components = None

# AB1000: stores geometry centered at each instance's connection point (STEP translation)
# Key = "BaseName__N", value = (centered_verts, faces, tx, ty, tz)
_ab_instances: Optional[Dict[str, Tuple[list, list, float, float, float]]] = None


# --- Loaders ---

def _make_loader(step_path, doc_id):
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TDocStd import TDocStd_Document
    from OCP.XCAFApp import XCAFApp_Application
    from OCP.XCAFDoc import XCAFDoc_DocumentTool
    from OCP.TDF import TDF_LabelSequence, TDF_Label
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDataStd import TDataStd_Name
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.BRep import BRep_Tool
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
    from OCP.TopoDS import TopoDS
    from OCP.BRepBndLib import BRepBndLib
    from OCP.Bnd import Bnd_Box
    from OCP.gp import gp_Trsf

    app = XCAFApp_Application.GetApplication_s()
    doc = TDocStd_Document(TCollection_ExtendedString(doc_id))
    app.NewDocument(TCollection_ExtendedString(doc_id), doc)
    reader = STEPCAFControl_Reader()
    reader.SetNameMode(True)
    reader.ReadFile(str(step_path))
    reader.Transfer(doc)
    shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    labels = TDF_LabelSequence()
    shape_tool.GetFreeShapes(labels)
    root = labels.Value(1)
    rbb = Bnd_Box()
    BRepBndLib.Add_s(shape_tool.GetShape_s(root), rbb)
    x0,y0,z0,x1,y1,z1 = rbb.Get()
    dims = (x1-x0, y1-y0, z1-z0)

    def get_name(label):
        attr = TDataStd_Name()
        if label.FindAttribute(TDataStd_Name.GetID_s(), attr):
            return attr.Get().ToExtString()
        return ""

    def tessellate(shape):
        BRepMesh_IncrementalMesh(shape, 2.0).Perform()
        verts, faces, offset = [], [], 0
        exp = TopExp_Explorer(shape, TopAbs_FACE)
        while exp.More():
            face = TopoDS.Face_s(exp.Current())
            loc = TopLoc_Location()
            tri = BRep_Tool.Triangulation_s(face, loc)
            if tri is not None:
                for i in range(1, tri.NbNodes()+1):
                    n = tri.Node(i)
                    if not loc.IsIdentity():
                        n = n.Transformed(loc.Transformation())
                    verts.append((n.X()-x0, n.Y()-y0, n.Z()-z0))
                rev = face.Orientation() == TopAbs_REVERSED
                for i in range(1, tri.NbTriangles()+1):
                    a,b,c = tri.Triangle(i).Get()
                    a-=1; b-=1; c-=1
                    if rev: a,b=b,a
                    faces.append((offset+a, offset+b, offset+c))
                offset += tri.NbNodes()
            exp.Next()
        return verts, faces

    components = {}
    counts = {}
    children = TDF_LabelSequence()
    shape_tool.GetComponents_s(root, children)
    for i in range(1, children.Size()+1):
        child = children.Value(i)
        ref = TDF_Label()
        name = get_name(ref if shape_tool.GetReferredShape_s(child, ref) else child)
        if not name:
            continue
        n = counts.get(name, 0)+1
        counts[name] = n

        # Extract STEP transform translation (connection point in global space)
        loc = shape_tool.GetLocation_s(child)
        trsf = loc.Transformation() if not loc.IsIdentity() else gp_Trsf()
        tx = trsf.TranslationPart().X() - x0
        ty = trsf.TranslationPart().Y() - y0
        tz = trsf.TranslationPart().Z() - z0

        verts, faces = tessellate(shape_tool.GetShape_s(child))
        key = f"{name}__{n}"
        components[key] = (verts, faces, tx, ty, tz)

    return dims, components


def _load():
    global _template_dims, _components
    if _components is not None:
        return
    _template_dims, raw = _make_loader(_TEMPLATE_PATH, "MDTV-CAF")
    # TerBox: merge duplicates, keep plain verts/faces
    merged = {}
    for key,(verts,faces,tx,ty,tz) in raw.items():
        base = key.split("__")[0]
        if base in merged:
            ev,ef = merged[base]
            off = len(ev)
            merged[base] = (ev+verts, ef+[(a+off,b+off,c+off) for a,b,c in faces])
        else:
            merged[base] = (verts, faces)
    _components = merged


def _load_ab():
    global _ab_instances
    if _ab_instances is not None:
        return
    _, raw = _make_loader(_AB_TEMPLATE_PATH, "MDTV-CAF-AB")
    _ab_instances = {
        k: v for k, v in raw.items()
        if not k.split("__")[0].startswith("Sechskant")
    }


# --- AB1000 geometry library ---

# Per-connector-instance: centered at STEP connection point, with translation stored
# Key: normalized corner tuple (nx, ny, nz) where each is 0 or 1
_ab_corner_map: Optional[Dict[Tuple, Tuple[list, list]]] = None
# Tube base geometries per axis (centered at bbox center)
_ab_tube_geom: Optional[Dict[str, Tuple[list, list]]] = None
# L-Ecke: 2-arm corner connector (Y + Z arms, no X arm)
_ab_l_ecke_geom: Optional[Tuple[list, list]] = None
# T-Ecke: T-shaped connector (two X arms + one Z arm)
_ab_t_ecke_geom: Optional[Tuple[list, list]] = None


def _build_ab_geom_library():
    global _ab_corner_map, _ab_tube_geom, _ab_l_ecke_geom, _ab_t_ecke_geom
    if _ab_corner_map is not None:
        return

    _ab_corner_map = {}
    _ab_tube_geom = {}

    for key, (verts, faces, tx, ty, tz) in _ab_instances.items():
        base = key.split("__")[0]
        if not verts:
            continue

        if base == "Y-Ecke":
            # Center at bbox center = junction center (confirmed: each Y-Ecke is exactly
            # 240x240x240mm with all arms ±120mm from the bbox center).
            # Using the STEP translation here was wrong — that point is offset from the
            # junction by up to 120mm depending on the connector's rotation.
            centered = _center_bbox(verts)
            # Corner assignment still uses the STEP translation (which normalises correctly)
            nx = round(tx / _AB_L)
            ny = round(ty / _AB_W)
            nz = round(tz / _AB_H)
            norm_corner = (nx, ny, nz)
            if norm_corner not in _ab_corner_map:
                _ab_corner_map[norm_corner] = (centered, faces)

        elif base == "L-Ecke" and _ab_l_ecke_geom is None:
            _ab_l_ecke_geom = (_center_bbox(verts), faces)

        elif base == "T Ecke" and _ab_t_ecke_geom is None:
            _ab_t_ecke_geom = (_center_bbox(verts), faces)

        elif base in _AB_TUBES and not _ab_tube_geom.get(_long_axis(verts)):
            axis = _long_axis(verts)
            _ab_tube_geom[axis] = (_center_tube_body(verts, axis), faces)

    # The 2 missing bottom-front corners need y+ arm openings.
    # Template has (0,1,0)→y- and (1,1,0)→y-, which are wrong for (0,0,0) and (1,0,0).
    # Mirror about Y (flip y) to turn y- arms into y+ arms.
    # Winding order must also be reversed to keep face normals correct after the Y-flip.
    for missing, source in [((0,0,0), (0,1,0)), ((1,0,0), (1,1,0))]:
        if missing not in _ab_corner_map and source in _ab_corner_map:
            sv, sf = _ab_corner_map[source]
            _ab_corner_map[missing] = (
                [(x, -y, z) for x, y, z in sv],
                [(a, c, b) for a, b, c in sf],  # reverse winding after Y-mirror
            )


# --- TerBox color helpers ---

def _component_color(name, config):
    if name in _FRAME or name in _ROOF:
        return _RAL_RGB.get(config.color, _DEFAULT_GREY)
    if name in _FLOOR:
        return _WPC_RGB.get(config.floorWpcColor.value, _DEFAULT_GREY) if config.floorWpcColor else (0.6,0.5,0.4)
    if name in _SIDE_WPC or name in _REAR_WPC:
        return _WPC_RGB.get(config.wpcColor.value, _DEFAULT_GREY) if config.wpcColor else _DEFAULT_GREY
    if name in _SIDE_FENCE or name in _REAR_FENCE:
        return (0.6,0.6,0.6)
    if name in _DOOR:
        return _RAL_RGB.get(config.shutterColor or config.color, _DEFAULT_GREY)
    return _DEFAULT_GREY

def _component_color_name(name, config):
    if name in _FRAME or name in _ROOF: return config.color
    if name in _FLOOR: return config.floorWpcColor.value if config.floorWpcColor else "wood"
    if name in _SIDE_WPC or name in _REAR_WPC: return config.wpcColor.value if config.wpcColor else ""
    if name in _SIDE_FENCE or name in _REAR_FENCE: return ""
    if name in _DOOR: return config.shutterColor or config.color
    return ""

def _active_components(config):
    active = list(_FRAME) + list(_ROOF)
    if config.floor == FloorOption.withFloor:
        active += list(_FLOOR)
    if config.wallHeight != WallHeight.none and config.wallMaterial is not None:
        mat = config.wallMaterial
        if mat in (WallMaterial.wpc, WallMaterial.realWood, WallMaterial.corrugatedSheet):
            active += list(_SIDE_WPC) + list(_REAR_WPC)
        elif mat in (WallMaterial.meshFence, WallMaterial.meshFenceWithPrivacy):
            active += list(_SIDE_FENCE) + list(_REAR_FENCE)
    if config.closureType == ClosureType.rollerDoor:
        active += list(_DOOR)
    if FeatureKey.carCharging in config.features or FeatureKey.bikeCharging in config.features:
        active += list(_CHARGING)
    if FeatureKey.bikeCharging in config.features:
        active += list(_BIKE)
    return active


# --- OBJ generators ---

def generate_preview_obj(config: TerBoxConfiguration, computed: ComputedConfig) -> str:
    if not _TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"STEP template not found at {_TEMPLATE_PATH}")
    _load()
    tw, th, tl = _template_dims
    length_cm = computed.module_count * computed.module_length_cm
    if config.customSize:
        try:
            width_cm = float(config.customSize.width)
            height_cm = float(config.customSize.height)
        except (ValueError, TypeError):
            width_cm, height_cm = _STANDARD_WIDTH_CM, _STANDARD_HEIGHT_CM
    else:
        width_cm, height_cm = _STANDARD_WIDTH_CM, _STANDARD_HEIGHT_CM

    s_length = (length_cm*10)/tw/1000 if tw else 0.001
    s_height = (height_cm*10)/tl/1000 if tl else 0.001
    s_depth  = (width_cm*10)/th/1000 if th else 0.001

    active = set(_active_components(config))
    lines = [f"# TER BOX {length_cm:.0f} x {width_cm:.0f} x {height_cm:.0f} cm"]
    vertex_offset = 1
    for name, (verts, faces) in _components.items():
        if name not in active or not verts: continue
        r,g,col_b = _component_color(name, config)
        color_name = _component_color_name(name, config)
        base_name = name.strip().replace(' ','_')
        group_name = f"{base_name}_{color_name}" if color_name else base_name
        lines.append(f"g {group_name}")
        for x,y,z in verts:
            lines.append(f"v {x*s_length:.6f} {z*s_height:.6f} {y*s_depth:.6f} {r:.3f} {g:.3f} {col_b:.3f}")
        for fa,fb,fc in faces:
            lines.append(f"f {vertex_offset+fa} {vertex_offset+fb} {vertex_offset+fc}")
        vertex_offset += len(verts)
    return "\n".join(lines)


def generate_ab1000_preview_obj(
    length_mm: float,
    width_mm:  float,
    height_mm: float,
    with_roof: bool = True,
    with_floor: bool = True,
    walls: str = "full",            # "full" | "half" | "none"
    wall_material: str | None = None,    # "wpc" | "realWood" | "glass" | "meshFence" | "meshFenceWithPrivacy" | "corrugatedSheet"
    wall_wpc_color: str | None = None,   # "cedar" | "darkGrey" | "teak" | "ipe" | "lightGrey"
    floor_material: str | None = None,   # "wpcFloor" | "woodFloor"
    floor_wpc_color: str | None = None,  # "cedar" | "darkGrey" | "teak" | "ipe" | "lightGrey"
    roller_door: bool = False,
    roller_door_color: str | None = None,  # RAL code e.g. "ral9005"
) -> str:
    if not _AB_TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"STEP template not found at {_AB_TEMPLATE_PATH}")
    _load_ab()
    _build_ab_geom_library()

    reg = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    arm = float(reg["y_corner"]["arm_length_mm"])

    L, W, H = length_mm, width_mm, height_mm
    # Scale factors relative to template
    sx = L / _AB_L
    sy = W / _AB_W
    sz = H / _AB_H

    instances: List[Tuple[str, list, list, tuple]] = []

    # --- 8 corners ---
    # Rule: junction center = box corner moved inward by arm in each arm direction.
    # Each Y-Ecke has 3 arms; each arm points toward the box interior (away from its corner).
    a = arm
    o = a - 75  # = 45mm: tube cross-section center offset in the perpendicular plane
    corner_defs = [
        ((0,1,0), (  a, W-a,   a)),   # nominal (0,W,0)
        ((1,1,0), (L-a, W-a,   a)),   # nominal (L,W,0)
        ((1,1,1), (L-a, W-a, H-a)),   # nominal (L,W,H)
        ((0,1,1), (  a, W-a, H-a)),   # nominal (0,W,H)
        ((0,0,1), (  a,   a, H-a)),   # nominal (0,0,H)
        ((1,0,1), (L-a,   a, H-a)),   # nominal (L,0,H)
        ((0,0,0), (  a,   a,   a)),   # nominal (0,0,0)
        ((1,0,0), (L-a,   a,   a)),   # nominal (L,0,0)
    ]
    # Front-bottom corners (0,0,0) and (1,0,0) lose their X arm when there is no floor
    # (front bottom tube is absent) — use L-Ecke (Y+Z arms only) there instead.
    _front_bottom_norms = {(0, 0, 0), (1, 0, 0)}
    for i, (norm, (px, py, pz)) in enumerate(corner_defs):
        if not with_floor and norm in _front_bottom_norms:
            if _ab_l_ecke_geom:
                lv, lf = _ab_l_ecke_geom
                # L-Ecke arm mouths are at (x_centered=0, perp=-75).
                # To align with tubes at (o, *, o) and (o, o, *) the junction must be
                # placed at (o, a, a) / (L-o, a, a) — NOT at (a, a, a) / (L-a, a, a).
                lx = o if norm[0] == 0 else L - o
                instances.append((f"L_Ecke__{i+1}", _place(lv, lx, py, pz), lf, _STEEL_RGB))
            continue
        geom = _ab_corner_map.get(norm)
        if not geom:
            continue
        cv, cf = geom
        instances.append((f"Y_Ecke__{i+1}", _place(cv, px, py, pz), cf, _STEEL_RGB))

    # --- Tubes: 100×100mm box, junction-to-junction length ---
    # Arm opening center is 75mm offset from junction center in each perp axis (measured from STEP).
    # Tube cross-section center must match arm opening center exactly.
    _needs_mid_post = L - 2 * o > 2500.0
    for axis, length, tube_positions in [
        ("x", L-2*a, [(L/2,   o,   o), (L/2, W-o,   o), (L/2,   o, H-o), (L/2, W-o, H-o)]),
        ("y", W-2*a, [(  o, W/2,   o), (L-o, W/2,   o), (  o, W/2, H-o), (L-o, W/2, H-o)]),
        ("z", H-2*a, [(  o,   o, H/2), (L-o,   o, H/2), (  o, W-o, H/2), (L-o, W-o, H/2)]),
    ]:
        tube_v, tube_f = _make_tube_box(axis, length)
        for i, pos in enumerate(tube_positions):
            if axis == "x" and i == 0 and not with_floor:
                continue  # front bottom tube omitted when no floor
            if axis == "x" and i in (2, 3) and _needs_mid_post:
                continue  # top front/back tubes replaced by two split halves below
            instances.append((f"Rohr_{axis.upper()}__{i+1}", _place(tube_v, *pos), tube_f, _STEEL_RGB))

    # --- Middle posts (front + back) when box length > 2500 mm inside frame ---
    if _needs_mid_post:
        # Each half-tube: junctions at (a, *, H-a) and (L/2, *, H-a) → length = (L/2-a) - 2a
        half_len  = L / 2 - 3 * a
        cx_left   = (a + L / 2) / 2
        cx_right  = (L / 2 + L - a) / 2
        split_tv, split_tf = _make_tube_box("x", half_len)
        mp_v, mp_f = _make_tube_box("z", H - 2 * a)

        # T-Ecke flipped: template Z arm points +Z (up); at post top it must point -Z (down)
        tv_flip, tf_flip = None, None
        if _ab_t_ecke_geom:
            tv_raw, tf_raw = _ab_t_ecke_geom
            tv_flip = [(x, y, -z) for x, y, z in tv_raw]
            tf_flip = [(fa, fc, fb) for fa, fb, fc in tf_raw]

        for y_pos, label in [(o, "Vorne"), (W - o, "Hinten")]:
            # Two split top tubes
            instances.append((f"Rohr_X_Top_{label}_L",
                               _place(split_tv, cx_left,  y_pos, H - o), split_tf, _STEEL_RGB))
            instances.append((f"Rohr_X_Top_{label}_R",
                               _place(split_tv, cx_right, y_pos, H - o), split_tf, _STEEL_RGB))
            # Middle post tube
            instances.append((f"Mittelpost_{label}",
                               _place(mp_v, L / 2, y_pos, H / 2), mp_f, _STEEL_RGB))
            # T-Ecke at top (Z-flipped so arm points down into post, X arms align with split tubes)
            if tv_flip is not None:
                instances.append((f"T_Ecke_{label}_Oben",
                                   _place(tv_flip, L / 2, y_pos, H - a), tf_flip, _STEEL_RGB))

        # Fußstück under front post only — when no floor the front bottom tube is absent
        if not with_floor:
            bv, bf = None, None
            for key, (verts, faces, tx, ty, tz) in _ab_instances.items():
                if key.split("__")[0] == "Fussplatte" and verts:
                    bv, bf = _center_bbox(verts), faces
                    break
            if bv:
                plate_top = max(v[2] for v in bv)  # 77.5 mm — place base at z=0, pin goes up
                instances.append(("Fussplatte_Mittelpost_Vorne",
                                   _place(bv, L / 2, o, plate_top), bf, _STEEL_RGB))

    # --- Roof: spans top frame, scales with box L×W ---
    if with_roof:
        rv, rf   = None, None   # roof panel (Dach Links)
        sub_v, sub_f = None, None  # roof substructure (Rohr Dach Links)
        for key, (verts, faces, tx, ty, tz) in _ab_instances.items():
            base = key.split("__")[0]
            if base == "Dach Links" and rv is None and verts:
                rv, rf = _center_bbox(verts), faces
            elif base == "Rohr Dach Links" and sub_v is None and verts:
                sub_v, sub_f = _center_bbox(verts), faces
            if rv is not None and sub_v is not None:
                break
        # Offsets measured from STEP: both components centered relative to top-tube centre (H-o)
        _SUB_CZ   = -5.3   # substructure bbox-centre is 5.3 mm below H-o
        _PANEL_CZ =  7.2   # panel bbox-centre is 7.2 mm above H-o
        # → the two pieces overlap ~62 mm in Z; the panel rests on the substructure cross-beams

        if sub_v is not None:
            sub_s = _scale_along(_scale_along(sub_v, "x", L - 2*o), "y", W - 2*o)
            instances.append(("Dach_Unterkonstruktion",
                               _place(sub_s, L/2, W/2, H - o + _SUB_CZ), sub_f, _STEEL_RGB))
        if rv is not None:
            rv_s = _scale_along(_scale_along(rv, "x", L - 2*o), "y", W - 2*o)
            instances.append(("Dach", _place(rv_s, L/2, W/2, H - o + _PANEL_CZ), rf, _STEEL_RGB))

        # Bolts connecting panel to substructure beams
        # 5 beams equally spaced in Y (o → W-o), 2 bolt columns in X, bolt spans overlap zone
        bolt_cz = H - o + (_SUB_CZ + _PANEL_CZ) / 2   # ≈ H-o+1, midpoint of overlap
        bv, bf  = _make_box(20.0, 20.0, 60.0)
        beam_ys = [o + i * (W - 2*o) / 4 for i in range(5)]
        bolt_xs = [o + (L - 2*o) / 3, o + 2 * (L - 2*o) / 3]
        for bi, by in enumerate(beam_ys):
            for xi, bx in enumerate(bolt_xs):
                instances.append((f"Bolt_Dach_{bi}_{xi}",
                                   _place(bv, bx, by, bolt_cz), bf, _STEEL_RGB))

    # --- Floor: sits inside bottom frame at tube-center height ---
    if with_floor:
        f_rgb = _floor_rgb(floor_material, floor_wpc_color)
        floor_t = 30.0
        lx_f, ly_f = L - 2 * o, W - 2 * o
        if floor_material in ("wpcFloor", "woodFloor"):
            instances.extend(_floor_plank_instances("Boden", lx_f, ly_f, floor_t, L/2, W/2, o, f_rgb))
        else:
            fv, ff = _make_box(lx_f, ly_f, floor_t)
            instances.append(("Boden", _place(fv, L/2, W/2, o), ff, f_rgb))

    # --- Walls ---
    if walls != "none":
        _wt  = 30.0   # panel thickness
        _pw  = 100.0  # middle post width (matches tube cross-section)
        # Panels span tube-center to tube-center; Schienen (mounted at tube centers) frame the edges
        panel_h = (H - 2 * o) / 2 if walls == "half" else H - 2 * o
        z_ctr   = o + panel_h / 2
        back_y  = W - o - _wt / 2   # panel face flush with back tube center
        left_x  = o + _wt / 2       # panel face flush with left tube center
        right_x = L - o - _wt / 2   # panel face flush with right tube center
        w_rgb = _wall_rgb(wall_material, wall_wpc_color)

        def _panel_items(name, lx, ly, lz, cx, cy, cz, corr_axis="x"):
            if wall_material in ("wpc", "realWood"):
                return _plank_instances(name, lx, ly, lz, cx, cy, cz, w_rgb)
            if wall_material == "corrugatedSheet":
                return _rib_instances(name, lx, ly, lz, cx, cy, cz, w_rgb, axis=corr_axis)
            pv, pf = _make_box(lx, ly, lz)
            return [(name, _place(pv, cx, cy, cz), pf, w_rgb)]

        def _panels_back():
            span = L - 2 * o
            if _needs_mid_post:
                half = (span - _pw) / 2
                cx_l = L/2 - _pw/2 - half/2
                cx_r = L/2 + _pw/2 + half/2
                instances.extend(_panel_items("Wand_Hinten_L", half, _wt, panel_h, cx_l, back_y, z_ctr))
                # Structural back middle post is added by the frame post loop above; skip wall post.
                if not _needs_mid_post:
                    mv, mf = _make_tube_box("z", panel_h)
                    instances.append(("Wand_Hinten_M", _place(mv, L/2, back_y, z_ctr), mf, _STEEL_RGB))
                instances.extend(_panel_items("Wand_Hinten_R", half, _wt, panel_h, cx_r, back_y, z_ctr))
            else:
                instances.extend(_panel_items("Wand_Hinten", span, _wt, panel_h, L/2, back_y, z_ctr))

        def _panels_side(x_pos, label):
            span = W - 2 * o
            if span > 2500.0:
                half = (span - _pw) / 2
                cy_v = W/2 - _pw/2 - half/2
                cy_h = W/2 + _pw/2 + half/2
                instances.extend(_panel_items(f"Wand_{label}_V", _wt, half, panel_h, x_pos, cy_v, z_ctr, "y"))
                mv, mf = _make_tube_box("z", panel_h)
                instances.append((f"Wand_{label}_M", _place(mv, x_pos, W/2, z_ctr), mf, _STEEL_RGB))
                instances.extend(_panel_items(f"Wand_{label}_H", _wt, half, panel_h, x_pos, cy_h, z_ctr, "y"))
            else:
                instances.extend(_panel_items(f"Wand_{label}", _wt, span, panel_h, x_pos, W/2, z_ctr, "y"))

        _panels_back()
        _panels_side(left_x,  "Links")
        _panels_side(right_x, "Rechts")

        # Schienen: C-channel rails centered on tubes, fully framing each panel on all 4 sides
        _sd, _sw = 18.0, 38.0  # rail depth and outer width (≥ panel thickness)
        # Back wall: vertical rails on left/right tubes, horizontal rails on bottom/top tubes
        sv_b,  sf_b  = _make_box(_sd, _sw, panel_h)       # vertical, depth in X
        sh_b,  sf_hb = _make_box(L - 2*o, _sw, _sd)       # horizontal, depth in Z
        # Side walls: vertical rails on front/back tubes, horizontal rails on bottom/top tubes
        sv_s,  sf_s  = _make_box(_sw, _sd, panel_h)       # vertical, depth in Y
        sh_s,  sf_hs = _make_box(_sw, W - 2*o, _sd)       # horizontal, depth in Z
        instances += [
            # Back wall
            ("Schiene_Hinten_L",   _place(sv_b,  o,   back_y, z_ctr), sf_b,  _STEEL_RGB),
            ("Schiene_Hinten_R",   _place(sv_b,  L-o, back_y, z_ctr), sf_b,  _STEEL_RGB),
            ("Schiene_Hinten_Bot", _place(sh_b,  L/2, back_y, o    ), sf_hb, _STEEL_RGB),
            ("Schiene_Hinten_Top", _place(sh_b,  L/2, back_y, H-o  ), sf_hb, _STEEL_RGB),
            # Left wall
            ("Schiene_Links_V",    _place(sv_s,  left_x, o,   z_ctr), sf_s,  _STEEL_RGB),
            ("Schiene_Links_H",    _place(sv_s,  left_x, W-o, z_ctr), sf_s,  _STEEL_RGB),
            ("Schiene_Links_Bot",  _place(sh_s,  left_x, W/2, o    ), sf_hs, _STEEL_RGB),
            ("Schiene_Links_Top",  _place(sh_s,  left_x, W/2, H-o  ), sf_hs, _STEEL_RGB),
            # Right wall
            ("Schiene_Rechts_V",   _place(sv_s,  right_x, o,   z_ctr), sf_s,  _STEEL_RGB),
            ("Schiene_Rechts_H",   _place(sv_s,  right_x, W-o, z_ctr), sf_s,  _STEEL_RGB),
            ("Schiene_Rechts_Bot", _place(sh_s,  right_x, W/2, o    ), sf_hs, _STEEL_RGB),
            ("Schiene_Rechts_Top", _place(sh_s,  right_x, W/2, H-o  ), sf_hs, _STEEL_RGB),
        ]

    # --- Roller door (open / rolled-up, housing on outside of front top tube) ---
    if roller_door:
        door_rgb = _RAL_RGB.get(roller_door_color, _STEEL_RGB) if roller_door_color else _STEEL_RGB
        door_w = L - 2 * o
        hd, hh = 200.0, 200.0
        housing_rgb = tuple(max(0.0, c - 0.08) for c in door_rgb)
        hv, hf = _make_box(door_w, hd, hh)
        # Outside face of front top tube: y = o - 50 = -5; housing sits just outside
        hy = o - 50 - hd / 2   # centre: 45 - 50 - 100 = -105 mm
        hz = H - o - hh / 2    # hangs just below top-tube centreline
        instances.append(("Rolltor_Gehaeuse", _place(hv, L/2, hy, hz), hf, housing_rgb))

    # --- Bike stands (always present) ---
    _load()
    stand_rgb = (0.62, 0.62, 0.64)
    total_w = L - 2 * o

    # Mounting rail — one piece spanning the full box width
    rv, rf = _components.get("Fahrradständer Befestigung", (None, None))
    if rv:
        rv = _center_bbox(rv)
        rv = _scale_along(rv, "x", total_w)
        rz = max(v[2] for v in rv) - min(v[2] for v in rv)
        instances.append(("Fahrradstaender_Halterung",
                           _place(rv, L/2, W - (o + 50) - 22.0, o + rz / 2), rf, stand_rgb))

    # Individual stand units: each slot ≥ 750 mm, count = floor(total_w / 750)
    sv, sf = _components.get("Fahrradständer 40*40", (None, None))
    if sv:
        sv = _center_bbox(sv)
        sv = _scale_along(sv, "x", total_w)
        sz = max(v[2] for v in sv) - min(v[2] for v in sv)
        cy_s = W - (o + 50) - 240.0
        cz_s = o + sz / 2
        instances.append(("Fahrradstaender",
                           _place(sv, L / 2, cy_s, cz_s), sf, stand_rgb))

    # --- Write OBJ ---
    lines = [f"# TER BOX AB1000 {L:.0f}x{W:.0f}x{H:.0f} mm"]
    vertex_offset = 1
    for name, verts, faces, rgb in instances:
        if not verts: continue
        lines.append(f"g {name.replace(' ','_')}")
        r, g, b = rgb
        for x,y,z in verts:
            lines.append(f"v {x/1000:.6f} {z/1000:.6f} {y/1000:.6f} {r:.3f} {g:.3f} {b:.3f}")
        for fa,fb,fc in faces:
            lines.append(f"f {vertex_offset+fa} {vertex_offset+fb} {vertex_offset+fc}")
        vertex_offset += len(verts)
    return "\n".join(lines)
