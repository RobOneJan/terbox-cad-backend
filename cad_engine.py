from pathlib import Path
from typing import Optional, Dict, Tuple, List

from models import (
    TerBoxConfiguration, ComputedConfig,
    FloorOption, WallHeight, WallMaterial, ClosureType, FeatureKey,
)

_TEMPLATE_PATH = Path(__file__).parent / "TER BOX 100x100.step"
_STANDARD_WIDTH_CM  = 249.4
_STANDARD_HEIGHT_CM = 230.0

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

_template_dims: Optional[Tuple[float, float, float]] = None
_components: Optional[Dict[str, Tuple[list, list]]] = None


def _load():
    global _template_dims, _components
    if _components is not None:
        return

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

    app = XCAFApp_Application.GetApplication_s()
    doc = TDocStd_Document(TCollection_ExtendedString("MDTV-CAF"))
    app.NewDocument(TCollection_ExtendedString("MDTV-CAF"), doc)

    reader = STEPCAFControl_Reader()
    reader.SetNameMode(True)
    reader.ReadFile(str(_TEMPLATE_PATH))
    reader.Transfer(doc)

    shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    labels = TDF_LabelSequence()
    shape_tool.GetFreeShapes(labels)
    root = labels.Value(1)
    root_shape = shape_tool.GetShape_s(root)
    rbb = Bnd_Box()
    BRepBndLib.Add_s(root_shape, rbb)
    x0, y0, z0, x1, y1, z1 = rbb.Get()
    _template_dims = (x1 - x0, y1 - y0, z1 - z0)

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
                for i in range(1, tri.NbNodes() + 1):
                    n = tri.Node(i)
                    if not loc.IsIdentity():
                        n = n.Transformed(loc.Transformation())
                    verts.append((n.X() - x0, n.Y() - y0, n.Z() - z0))
                rev = face.Orientation() == TopAbs_REVERSED
                for i in range(1, tri.NbTriangles() + 1):
                    a, b, c = tri.Triangle(i).Get()
                    a -= 1; b -= 1; c -= 1
                    if rev:
                        a, b = b, a
                    faces.append((offset + a, offset + b, offset + c))
                offset += tri.NbNodes()
            exp.Next()
        return verts, faces

    _components = {}
    children = TDF_LabelSequence()
    shape_tool.GetComponents_s(root, children)
    for i in range(1, children.Size() + 1):
        child = children.Value(i)
        ref = TDF_Label()
        if shape_tool.GetReferredShape_s(child, ref):
            name = get_name(ref)
        else:
            name = get_name(child)
        if name:
            _components[name] = tessellate(shape_tool.GetShape_s(child))


def _component_color(name: str, config: TerBoxConfiguration) -> Tuple[float, float, float]:
    if name in _FRAME or name in _ROOF:
        return _RAL_RGB.get(config.color, _DEFAULT_GREY)
    if name in _FLOOR:
        if config.floorWpcColor:
            return _WPC_RGB.get(config.floorWpcColor.value, _DEFAULT_GREY)
        return (0.6, 0.5, 0.4)
    if name in _SIDE_WPC or name in _REAR_WPC:
        if config.wpcColor:
            return _WPC_RGB.get(config.wpcColor.value, _DEFAULT_GREY)
        return _DEFAULT_GREY
    if name in _SIDE_FENCE or name in _REAR_FENCE:
        return (0.6, 0.6, 0.6)
    if name in _DOOR:
        color_key = config.shutterColor or config.color
        return _RAL_RGB.get(color_key, _DEFAULT_GREY)
    return _DEFAULT_GREY


def _component_color_name(name: str, config: TerBoxConfiguration) -> str:
    if name in _FRAME or name in _ROOF:
        return config.color
    if name in _FLOOR:
        return config.floorWpcColor.value if config.floorWpcColor else "wood"
    if name in _SIDE_WPC or name in _REAR_WPC:
        return config.wpcColor.value if config.wpcColor else ""
    if name in _SIDE_FENCE or name in _REAR_FENCE:
        return ""
    if name in _DOOR:
        return config.shutterColor or config.color
    return ""


def _active_components(config: TerBoxConfiguration) -> List[str]:
    active: List[str] = list(_FRAME) + list(_ROOF)

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


def generate_preview_obj(config: TerBoxConfiguration, computed: ComputedConfig) -> str:
    if not _TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"STEP template not found at {_TEMPLATE_PATH}")

    _load()

    tw, th, tl = _template_dims

    length_cm = computed.module_count * computed.module_length_cm
    if config.customSize:
        try:
            width_cm  = float(config.customSize.width)
            height_cm = float(config.customSize.height)
        except (ValueError, TypeError):
            width_cm  = _STANDARD_WIDTH_CM
            height_cm = _STANDARD_HEIGHT_CM
    else:
        width_cm  = _STANDARD_WIDTH_CM
        height_cm = _STANDARD_HEIGHT_CM

    s_length = (length_cm * 10) / tw / 1000 if tw else 0.001
    s_height = (height_cm * 10) / tl / 1000 if tl else 0.001
    s_depth  = (width_cm  * 10) / th / 1000 if th else 0.001

    active = set(_active_components(config))
    lines = [f"# TER BOX {length_cm:.0f} x {width_cm:.0f} x {height_cm:.0f} cm"]
    vertex_offset = 1

    for name, (verts, faces) in _components.items():
        if name not in active or not verts:
            continue
        r, g, col_b = _component_color(name, config)
        color_name = _component_color_name(name, config)
        base_name = name.strip().replace(' ', '_')
        group_name = f"{base_name}_{color_name}" if color_name else base_name
        lines.append(f"g {group_name}")
        for x, y, z in verts:
            lines.append(f"v {x*s_length:.6f} {z*s_height:.6f} {y*s_depth:.6f} {r:.3f} {g:.3f} {col_b:.3f}")
        for fa, fb, fc in faces:
            lines.append(f"f {vertex_offset+fa} {vertex_offset+fb} {vertex_offset+fc}")
        vertex_offset += len(verts)

    return "\n".join(lines)
